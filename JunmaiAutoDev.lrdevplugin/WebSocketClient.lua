-- WebSocketClient.lua
--
-- WebSocket client for bidirectional communication with Python bridge
-- Provides real-time progress updates and job notifications

local LrTasks = import 'LrTasks'
local LrHttp = import 'LrHttp'
local LrLogger = import 'LrLogger'
local LrDate = import 'LrDate'
local JSON = require 'Utils.JSON'

local log = LrLogger('JunmaiAutoDevWebSocket')
log:enable("logfile")

local WebSocketClient = {}

-- Configuration
local WS_URL = "ws://127.0.0.1:5100/ws"
local HTTP_FALLBACK_URL = "http://127.0.0.1:5100"
local RECONNECT_DELAY = 5 -- seconds
local PING_INTERVAL = 30 -- seconds
local MAX_RECONNECT_ATTEMPTS = 10

-- State
local isConnected = false
local reconnectAttempts = 0
local messageHandlers = {}
local eventListeners = {}
local lastPingTime = 0
local clientId = nil
local connectionTask = nil

---
-- Initialize WebSocket client
-- Note: Lua SDK doesn't support native WebSocket, so we use HTTP long-polling as fallback
--
function WebSocketClient.init()
    log:info("Initializing WebSocket client (HTTP fallback mode)")
    
    -- Register default handlers
    WebSocketClient.registerHandler('connection_established', function(message)
        clientId = message.client_id
        log:info("Connection established. Client ID: " .. tostring(clientId))
        isConnected = true
        reconnectAttempts = 0
        
        -- Register this client
        WebSocketClient.send({
            type = 'register',
            client_type = 'lightroom',
            client_name = 'Lightroom Classic Plugin',
            version = '2.0'
        })
        
        -- Subscribe to relevant channels
        WebSocketClient.send({
            type = 'subscribe',
            channels = {'jobs', 'system', 'photos'}
        })
    end)
    
    WebSocketClient.registerHandler('pong', function(message)
        lastPingTime = LrDate.currentTime()
        log:trace("Received pong from server")
    end)
    
    WebSocketClient.registerHandler('error', function(message)
        log:error("Server error: " .. tostring(message.error))
    end)
    
    -- Start connection task
    WebSocketClient.connect()
end

---
-- Connect to WebSocket server (HTTP fallback)
--
function WebSocketClient.connect()
    if connectionTask then
        log:warn("Connection task already running")
        return
    end
    
    connectionTask = LrTasks.startAsyncTask(function()
        log:info("Starting connection task")
        
        while reconnectAttempts < MAX_RECONNECT_ATTEMPTS do
            if not isConnected then
                log:info("Attempting to connect... (attempt " .. (reconnectAttempts + 1) .. ")")
                
                -- Try to establish connection via HTTP handshake
                local success = WebSocketClient._attemptConnection()
                
                if success then
                    log:info("Connection successful")
                    
                    -- Start ping task
                    WebSocketClient._startPingTask()
                    
                    -- Start polling for messages
                    WebSocketClient._startPollingTask()
                    
                    break
                else
                    reconnectAttempts = reconnectAttempts + 1
                    log:warn("Connection failed. Retrying in " .. RECONNECT_DELAY .. " seconds...")
                    LrTasks.sleep(RECONNECT_DELAY)
                end
            else
                break
            end
        end
        
        if reconnectAttempts >= MAX_RECONNECT_ATTEMPTS then
            log:error("Max reconnection attempts reached. Giving up.")
        end
    end)
end

---
-- Attempt connection to server
-- @return boolean success
--
function WebSocketClient._attemptConnection()
    local url = HTTP_FALLBACK_URL .. "/ws/handshake"
    
    local response, headers = LrHttp.post(url, JSON.encode({
        client_type = 'lightroom',
        protocol_version = '1.0'
    }), {
        { field = 'Content-Type', value = 'application/json' }
    })
    
    if response then
        local ok, data = pcall(JSON.decode, response)
        if ok and data and data.success then
            clientId = data.client_id
            isConnected = true
            reconnectAttempts = 0
            
            -- Notify listeners
            WebSocketClient._notifyListeners('connected', {})
            
            return true
        end
    end
    
    return false
end

---
-- Start ping task to keep connection alive
--
function WebSocketClient._startPingTask()
    LrTasks.startAsyncTask(function()
        while isConnected do
            LrTasks.sleep(PING_INTERVAL)
            
            if isConnected then
                WebSocketClient.send({
                    type = 'ping',
                    timestamp = LrDate.currentTime()
                })
            end
        end
    end)
end

---
-- Start polling task for receiving messages (HTTP fallback)
--
function WebSocketClient._startPollingTask()
    LrTasks.startAsyncTask(function()
        log:info("Starting message polling task")
        
        while isConnected do
            -- Poll for messages
            local url = HTTP_FALLBACK_URL .. "/ws/poll?client_id=" .. tostring(clientId)
            
            local response, headers = LrHttp.get(url)
            
            if response then
                local ok, data = pcall(JSON.decode, response)
                if ok and data and data.messages then
                    -- Process received messages
                    for _, message in ipairs(data.messages) do
                        WebSocketClient._handleMessage(message)
                    end
                end
            else
                -- Connection lost
                log:warn("Polling failed. Connection may be lost.")
                isConnected = false
                WebSocketClient._notifyListeners('disconnected', {})
                
                -- Attempt reconnection
                LrTasks.sleep(RECONNECT_DELAY)
                WebSocketClient.connect()
                break
            end
            
            -- Short sleep between polls
            LrTasks.sleep(1)
        end
    end)
end

---
-- Send message to server
-- @param message table Message to send
--
function WebSocketClient.send(message)
    if not isConnected then
        log:warn("Cannot send message: not connected")
        return false
    end
    
    if not message.type then
        log:error("Message must have a 'type' field")
        return false
    end
    
    -- Add timestamp if not present
    if not message.timestamp then
        message.timestamp = LrDate.currentTime()
    end
    
    -- Send via HTTP POST (fallback)
    local url = HTTP_FALLBACK_URL .. "/ws/send"
    
    local payload = JSON.encode({
        client_id = clientId,
        message = message
    })
    
    local response, headers = LrHttp.post(url, payload, {
        { field = 'Content-Type', value = 'application/json' }
    })
    
    if response then
        local ok, data = pcall(JSON.decode, response)
        if ok and data and data.success then
            log:trace("Message sent: " .. message.type)
            return true
        end
    end
    
    log:error("Failed to send message: " .. message.type)
    return false
end

---
-- Handle incoming message
-- @param message table Received message
--
function WebSocketClient._handleMessage(message)
    if not message or not message.type then
        log:warn("Received invalid message")
        return
    end
    
    local msgType = message.type
    log:trace("Received message: " .. msgType)
    
    -- Call registered handler
    local handler = messageHandlers[msgType]
    if handler then
        local ok, err = pcall(handler, message)
        if not ok then
            log:error("Error in message handler for " .. msgType .. ": " .. tostring(err))
        end
    else
        log:trace("No handler registered for message type: " .. msgType)
    end
    
    -- Notify event listeners
    WebSocketClient._notifyListeners(msgType, message)
end

---
-- Register message handler
-- @param messageType string Type of message to handle
-- @param handler function Handler function(message)
--
function WebSocketClient.registerHandler(messageType, handler)
    messageHandlers[messageType] = handler
    log:info("Registered handler for message type: " .. messageType)
end

---
-- Add event listener
-- @param eventType string Event type to listen for
-- @param listener function Listener function(data)
--
function WebSocketClient.addEventListener(eventType, listener)
    if not eventListeners[eventType] then
        eventListeners[eventType] = {}
    end
    table.insert(eventListeners[eventType], listener)
    log:info("Added event listener for: " .. eventType)
end

---
-- Remove event listener
-- @param eventType string Event type
-- @param listener function Listener function to remove
--
function WebSocketClient.removeEventListener(eventType, listener)
    if eventListeners[eventType] then
        for i, l in ipairs(eventListeners[eventType]) do
            if l == listener then
                table.remove(eventListeners[eventType], i)
                log:info("Removed event listener for: " .. eventType)
                break
            end
        end
    end
end

---
-- Notify event listeners
-- @param eventType string Event type
-- @param data table Event data
--
function WebSocketClient._notifyListeners(eventType, data)
    if eventListeners[eventType] then
        for _, listener in ipairs(eventListeners[eventType]) do
            local ok, err = pcall(listener, data)
            if not ok then
                log:error("Error in event listener for " .. eventType .. ": " .. tostring(err))
            end
        end
    end
end

---
-- Send job progress update
-- @param jobId string Job ID
-- @param stage string Current stage
-- @param progress number Progress percentage (0-100)
-- @param message string Optional progress message
-- @param details table Optional additional details
--
function WebSocketClient.sendJobProgress(jobId, stage, progress, message, details)
    return WebSocketClient.send({
        type = 'job_progress',
        job_id = jobId,
        stage = stage,
        progress = progress,
        message = message or '',
        details = details or {}
    })
end

---
-- Send stage completion notification
-- @param jobId string Job ID
-- @param stage string Completed stage
-- @param result table Optional stage result data
--
function WebSocketClient.sendStageComplete(jobId, stage, result)
    return WebSocketClient.send({
        type = 'stage_completed',
        job_id = jobId,
        stage = stage,
        result = result or {}
    })
end

---
-- Send photo information
-- @param jobId string Job ID
-- @param photoId number Photo database ID
-- @param photoData table Photo metadata and analysis
--
function WebSocketClient.sendPhotoInfo(jobId, photoId, photoData)
    return WebSocketClient.send({
        type = 'photo_info',
        job_id = jobId,
        photo_id = photoId,
        photo_data = photoData
    })
end

---
-- Send job start notification
-- @param jobId string Job ID
-- @param photoId number Photo database ID
-- @param photoInfo table Basic photo information
--
function WebSocketClient.sendJobStart(jobId, photoId, photoInfo)
    return WebSocketClient.send({
        type = 'job_started',
        job_id = jobId,
        photo_id = photoId,
        photo_info = photoInfo or {}
    })
end

---
-- Send job completion notification
-- @param jobId string Job ID
-- @param success boolean Whether job succeeded
-- @param result table Optional result data
-- @param duration number Optional job duration in seconds
--
function WebSocketClient.sendJobComplete(jobId, success, result, duration)
    return WebSocketClient.send({
        type = success and 'job_completed' or 'job_failed',
        job_id = jobId,
        success = success,
        result = result or {},
        duration = duration
    })
end

---
-- Send error notification with detailed context
-- @param jobId string Job ID (optional)
-- @param errorType string Error type
-- @param errorMessage string Error message
-- @param errorDetails table Detailed error information
-- @param stage string Stage where error occurred (optional)
--
function WebSocketClient.sendError(jobId, errorType, errorMessage, errorDetails, stage)
    return WebSocketClient.send({
        type = 'error_occurred',
        job_id = jobId,
        error_type = errorType,
        error_message = errorMessage,
        error_details = errorDetails or {},
        stage = stage
    })
end

---
-- Send processing metrics
-- @param jobId string Job ID
-- @param metrics table Processing metrics (time, memory, etc.)
--
function WebSocketClient.sendMetrics(jobId, metrics)
    return WebSocketClient.send({
        type = 'processing_metrics',
        job_id = jobId,
        metrics = metrics
    })
end

---
-- Check if connected
-- @return boolean Connection status
--
function WebSocketClient.isConnected()
    return isConnected
end

---
-- Get client ID
-- @return string Client ID or nil
--
function WebSocketClient.getClientId()
    return clientId
end

---
-- Disconnect from server
--
function WebSocketClient.disconnect()
    if isConnected then
        log:info("Disconnecting from server")
        
        -- Send disconnect message
        WebSocketClient.send({
            type = 'disconnect',
            client_id = clientId
        })
        
        isConnected = false
        clientId = nil
        
        WebSocketClient._notifyListeners('disconnected', {})
    end
end

---
-- Reconnect to server
--
function WebSocketClient.reconnect()
    log:info("Reconnecting to server")
    WebSocketClient.disconnect()
    reconnectAttempts = 0
    LrTasks.sleep(1)
    WebSocketClient.connect()
end

log:info("WebSocketClient module loaded")

return WebSocketClient
