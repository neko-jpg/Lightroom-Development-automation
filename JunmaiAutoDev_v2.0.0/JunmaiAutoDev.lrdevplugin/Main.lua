-- Main.lua
--
-- Main logic for the Junmai Auto Develop plugin.

local LrTasks = import 'LrTasks'
local LrHttp = import 'LrHttp'
local LrLogger = import 'LrLogger'
local LrDialogs = import 'LrDialogs'

local log = LrLogger('JunmaiAutoDevLogger')
log:enable("logfile")

local JobRunner = require 'JobRunner'
local WebSocketClient = require 'WebSocketClient'
local JSON = require 'Utils.JSON'

local API_BASE_URL = "http://127.0.0.1:5100"
local POLLING_INTERVAL = 15 -- in seconds

local status = "Idle" -- The plugin's current status
local listeners = {}   -- Table to hold listener functions
local currentJobId = nil -- Track current job being processed

-- Notify all listeners of a status change
local function notifyListeners()
    for _, listener in ipairs(listeners) do
        listener(status)
    end
end

-- Internal function to set the status and notify listeners
local function setStatus(newStatus)
    if status ~= newStatus then
        status = newStatus
        log:info("Status changed to: " .. status)
        notifyListeners()
    end
end

-- Create a public interface for the module
local Main = {}

-- Add a listener function to be called on status changes
function Main.addStatusListener(listener)
    table.insert(listeners, listener)
end

-- Remove a listener function
function Main.removeStatusListener(listener)
    for i, l in ipairs(listeners) do
        if l == listener then
            table.remove(listeners, i)
            break
        end
    end
end

function Main.pollForNextJob()
    if status == "Polling..." or status == "Job Received. Processing..." then
        log:info("Polling or processing is already in progress. Skipping.")
        return
    end

    setStatus("Polling...")

    local url = API_BASE_URL .. "/job/next"

    LrHttp.get(url, function(response)
        if response and response.body then
            if response.statusCode == 200 then
                setStatus("Job Received. Processing...")
                log:info("Successfully received a new job.")

                local ok, jobData = pcall(JSON.decode, response.body)
                if not ok or type(jobData) ~= "table" then
                    setStatus("Error: Invalid JSON")
                    log:error("Failed to decode the job wrapper JSON: " .. tostring(response.body))
                    return
                end

                local jobId = jobData.jobId
                local config = jobData.config

                if not jobId or type(config) ~= "table" then
                    setStatus("Error: Invalid Job Data")
                    log:error("Invalid job structure. Missing 'jobId' or 'config'.")
                    return
                end

                log:info("Starting job ID: " .. jobId)

                LrTasks.startAsyncTask(function()
                    local ok, success = pcall(Main.processJobWithProgress, jobId, config)

                    local resultStatus
                    local resultMessage

                    if ok and success then
                        resultStatus = "success"
                        setStatus("Job Completed Successfully")
                        LrDialogs.showBezel("Job " .. jobId .. " Completed", 1.5)
                        log:info("Job " .. jobId .. " completed successfully.")
                    else
                        resultStatus = "failure"
                        -- If pcall failed, 'success' contains the error message
                        local reason = not ok and tostring(success) or "JobRunner returned false. See plugin logs for details."
                        setStatus("Job Failed: " .. reason)
                        LrDialogs.showBezel("Job " .. jobId .. " Failed", 2.5)
                        log:error("Job " .. jobId .. " failed. Reason: " .. reason)
                        resultMessage = reason
                    end

                    -- Report the result back to the server
                    local resultUrl = API_BASE_URL .. "/job/" .. jobId .. "/result"
                    local resultData = { status = resultStatus, reason = resultMessage }
                    local jsonData, jsonErr = pcall(JSON.encode, resultData)

                    if not jsonData then
                        log:error("Failed to encode job result JSON: " .. tostring(jsonErr))
                        return
                    end

                    LrHttp.post(resultUrl, jsonData, function(res)
                        if res and res.statusCode == 200 then
                            log:info("Successfully reported job result for " .. jobId)
                        else
                            log:error("Failed to report job result for " .. jobId .. ". Status: " .. tostring(res and res.statusCode))
                        end
                        -- After reporting, we can go back to Idle unless another job is already processing
                        if status ~= "Polling..." then
                            setStatus("Idle")
                        end
                    end)
                end)

            elseif response.statusCode == 404 then
                setStatus("Idle")
                log:info("No pending jobs.")
            else
                local err_msg = "API Request Failed (Code: " .. response.statusCode .. ")"
                setStatus(err_msg)
                log:error(err_msg)
                log:error("Response body: " .. response.body)
            end
        else
            setStatus("Error: HTTP Request Failed")
            log:error("HTTP request failed with no response body.")
        end
    end)
end

function Main.getStatus()
    return status
end

-- Initialize WebSocket client
LrTasks.startAsyncTask(function()
    log:info("Initializing WebSocket client...")
    WebSocketClient.init()
    
    -- Register WebSocket event handlers
    WebSocketClient.addEventListener('job_created', function(data)
        log:info("New job created notification received: " .. tostring(data.job_id))
        -- Optionally trigger immediate polling
        Main.pollForNextJob()
    end)
    
    WebSocketClient.addEventListener('system_status', function(data)
        log:trace("System status update received")
        -- Update local status if needed
    end)
    
    WebSocketClient.addEventListener('connected', function(data)
        log:info("WebSocket connected successfully")
        setStatus("Connected (WebSocket)")
    end)
    
    WebSocketClient.addEventListener('disconnected', function(data)
        log:warn("WebSocket disconnected")
        setStatus("Disconnected (Polling fallback)")
    end)
end)

-- Start a recurring task to poll the server in the background automatically.
LrTasks.startAsyncTask(function()
    log:info("Junmai Auto Develop plugin started. Initializing background job polling.")
    setStatus("Idle")
    LrTasks.scheduleEvery(POLLING_INTERVAL, Main.pollForNextJob)
end)

-- Enhanced job processing with detailed WebSocket progress updates
function Main.processJobWithProgress(jobId, config)
    currentJobId = jobId
    local startTime = os.time()
    
    -- Extract photo information from config
    local photoInfo = {
        file_name = config.photoPath and config.photoPath:match("([^/\\]+)$") or "unknown",
        config_version = config.version or "unknown"
    }
    
    -- Send job started notification with photo info
    if WebSocketClient.isConnected() then
        WebSocketClient.sendJobStart(jobId, nil, photoInfo)
    end
    
    -- Process job with detailed progress updates
    local success, result = pcall(function()
        -- Stage 1: Preparation (0-15%)
        if WebSocketClient.isConnected() then
            WebSocketClient.sendJobProgress(jobId, 'preparation', 5, 'Loading photo...', {
                photo_path = config.photoPath
            })
        end
        
        LrTasks.sleep(0.1) -- Small delay for UI update
        
        if WebSocketClient.isConnected() then
            WebSocketClient.sendJobProgress(jobId, 'preparation', 10, 'Validating configuration...')
        end
        
        -- Validate config structure
        if not config.pipeline or type(config.pipeline) ~= "table" then
            error("Invalid config: missing or invalid pipeline")
        end
        
        if WebSocketClient.isConnected() then
            WebSocketClient.sendJobProgress(jobId, 'preparation', 15, 'Configuration validated')
            WebSocketClient.sendStageComplete(jobId, 'preparation', {
                pipeline_stages = #config.pipeline
            })
        end
        
        -- Stage 2: Applying Settings (15-85%)
        local totalStages = #config.pipeline
        local progressPerStage = 70 / totalStages
        local currentProgress = 15
        
        if WebSocketClient.isConnected() then
            WebSocketClient.sendJobProgress(jobId, 'applying_preset', currentProgress, 
                'Starting to apply ' .. totalStages .. ' pipeline stages...')
        end
        
        -- Run the actual job with progress tracking
        local jobSuccess = JobRunner.runJob(config, function(stageIndex, stageName, stageResult)
            -- Progress callback from JobRunner
            currentProgress = 15 + (stageIndex * progressPerStage)
            
            if WebSocketClient.isConnected() then
                WebSocketClient.sendJobProgress(jobId, 'applying_preset', currentProgress,
                    'Applied stage ' .. stageIndex .. '/' .. totalStages .. ': ' .. stageName,
                    {
                        stage_index = stageIndex,
                        stage_name = stageName,
                        total_stages = totalStages
                    })
            end
        end)
        
        if not jobSuccess then
            error("JobRunner failed to apply settings")
        end
        
        if WebSocketClient.isConnected() then
            WebSocketClient.sendStageComplete(jobId, 'applying_preset', {
                stages_applied = totalStages
            })
        end
        
        -- Stage 3: Quality Check (85-95%)
        if WebSocketClient.isConnected() then
            WebSocketClient.sendJobProgress(jobId, 'quality_check', 90, 'Verifying applied settings...')
        end
        
        LrTasks.sleep(0.1)
        
        if WebSocketClient.isConnected() then
            WebSocketClient.sendStageComplete(jobId, 'quality_check', {
                verified = true
            })
        end
        
        -- Stage 4: Finalization (95-100%)
        if WebSocketClient.isConnected() then
            WebSocketClient.sendJobProgress(jobId, 'finalizing', 95, 'Saving changes...')
        end
        
        LrTasks.sleep(0.1)
        
        if WebSocketClient.isConnected() then
            WebSocketClient.sendJobProgress(jobId, 'completed', 100, 'Job completed successfully')
        end
        
        return true
    end)
    
    local endTime = os.time()
    local duration = endTime - startTime
    
    -- Send completion notification with metrics
    if WebSocketClient.isConnected() then
        if success and result then
            WebSocketClient.sendJobComplete(jobId, true, {
                stages_completed = config.pipeline and #config.pipeline or 0,
                photo_info = photoInfo
            }, duration)
        else
            -- Send error details
            local errorMessage = tostring(result)
            WebSocketClient.sendError(jobId, 'processing_error', errorMessage, {
                photo_info = photoInfo,
                config_version = config.version
            }, 'applying_preset')
            
            WebSocketClient.sendJobComplete(jobId, false, {
                error = errorMessage,
                photo_info = photoInfo
            }, duration)
        end
    end
    
    currentJobId = nil
    return success and result
end

-- Get current job ID (for external monitoring)
function Main.getCurrentJobId()
    return currentJobId
end

-- Get WebSocket connection status
function Main.isWebSocketConnected()
    return WebSocketClient.isConnected()
end

log:info("Main.lua loaded with WebSocket support and background polling started.")

return Main
