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
local JSON = require 'Utils.JSON'

local API_BASE_URL = "http://127.0.0.1:5100"
local POLLING_INTERVAL = 15 -- in seconds

local status = "Idle" -- The plugin's current status
local listeners = {}   -- Table to hold listener functions

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
                    local ok, success = pcall(JobRunner.runJob, config)

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

-- Start a recurring task to poll the server in the background automatically.
LrTasks.startAsyncTask(function()
    log:info("Junmai Auto Develop plugin started. Initializing background job polling.")
    setStatus("Idle")
    LrTasks.scheduleEvery(POLLING_INTERVAL, Main.pollForNextJob)
end)

log:info("Main.lua loaded and background polling started.")

return Main
