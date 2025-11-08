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

-- Create a public interface for the module
local Main = {}

function Main.pollForNextJob()
    if status == "Polling..." then
        log:info("Polling is already in progress.")
        return
    end

    log:info("Polling for next job...")
    status = "Polling..."

    local url = API_BASE_URL .. "/job/next"

    LrHttp.get(url, function(response)
        if response and response.body then
            if response.statusCode == 200 then
                status = "Job Received. Processing..."
                log:info("Successfully received a new job.")

                local ok, jobData = pcall(JSON.decode, response.body)
                if not ok or type(jobData) ~= "table" then
                    status = "Error: Invalid JSON"
                    log:error("Failed to decode the job wrapper JSON: " .. tostring(response.body))
                    return
                end

                local jobId = jobData.jobId
                local config = jobData.config

                if not jobId or type(config) ~= "table" then
                    status = "Error: Invalid Job Data"
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
                        status = "Job Completed Successfully"
                        LrDialogs.showBezel(status, 1.5)
                        log:info("Job " .. jobId .. " completed successfully.")
                    else
                        resultStatus = "failure"
                        status = "Job Failed. See logs."
                        LrDialogs.showBezel(status, 2.5)
                        -- If pcall failed, 'success' contains the error message
                        local reason = not ok and tostring(success) or "JobRunner returned false. See plugin logs for details."
                        log:error("Job " .. jobId .. " failed. Reason: " .. reason)
                        resultMessage = reason
                    end

                    -- Report the result back to the server
                    local url = API_BASE_URL .. "/job/" .. jobId .. "/result"
                    local resultData = { status = resultStatus, reason = resultMessage }
                    local jsonData, jsonErr = pcall(JSON.encode, resultData)

                    if not jsonData then
                         log:error("Failed to encode job result JSON: " .. tostring(jsonErr))
                         return
                    end

                    LrHttp.post(url, jsonData, function(res)
                        if res and res.statusCode == 200 then
                            log:info("Successfully reported job result for " .. jobId)
                        else
                            log:error("Failed to report job result for " .. jobId .. ". Status: " .. tostring(res and res.statusCode))
                        end
                    end)
                end)

            elseif response.statusCode == 404 then
                status = "Idle - No pending jobs."
                log:info("No pending jobs.")
            else
                status = "Error: API Request Failed"
                log:error("Received an unexpected status code: " .. response.statusCode)
                log:error("Response body: " .. response.body)
            end
        else
            status = "Error: HTTP Request Failed"
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
    LrTasks.scheduleEvery(POLLING_INTERVAL, Main.pollForNextJob)
end)

log:info("Main.lua loaded and background polling started.")

return Main
