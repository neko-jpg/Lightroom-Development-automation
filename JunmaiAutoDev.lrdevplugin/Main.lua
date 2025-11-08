-- Main.lua
--
-- Main logic for the Junmai Auto Develop plugin.

local LrTasks = import 'LrTasks'
local LrHttp = import 'LrHttp'
local LrLogger = import 'LrLogger'

-- It is recommended to create a logger for your plugin.
-- The logger can be viewed via the "Show in Console" button in the Plug-in Manager.
local log = LrLogger('JunmaiAutoDevLogger')
log:enable("logfile") -- This will write logs to a file.

local JobRunner = require 'JobRunner'
local JSON = require 'Utils.JSON'

local API_BASE_URL = "http://127.0.0.1:5100"
local POLLING_INTERVAL = 5 -- in seconds

local function pollForNextJob()
    log:info("Polling for next job...")

    local url = API_BASE_URL .. "/job/next"

    LrHttp.get(url, function(response)
        if response and response.body then
            if response.statusCode == 200 then
                log:info("Successfully received a new job.")

                -- Safely decode the wrapper JSON to get job details
                local ok, jobData = pcall(JSON.decode, response.body)
                if not ok or type(jobData) ~= "table" then
                    log:error("Failed to decode the job wrapper JSON: " .. tostring(response.body))
                    return
                end

                local jobId = jobData.jobId
                local config = jobData.config

                if not jobId or type(config) ~= "table" then
                    log:error("Invalid job structure. Missing 'jobId' or 'config'.")
                    return
                end

                log:info("Starting job ID: " .. jobId)

                -- Run the job in a separate, non-blocking task
                LrTasks.startAsyncTask(function()
                    JobRunner.runJob(config)
                end)

            elseif response.statusCode == 404 then
                log:info("No pending jobs.")
            else
                log:error("Received an unexpected status code: " .. response.statusCode)
                log:error("Response body: " .. response.body)
            end
        else
            log:error("HTTP request failed with no response body.")
        end
    end)
end

-- Start a recurring task to poll the local bridge server.
-- This task will run in the background.
LrTasks.startAsyncTask(function()
    log:info("Junmai Auto Develop plugin started. Initializing job polling.")
    LrTasks.scheduleEvery(POLLING_INTERVAL, pollForNextJob)
end)

log:info("Main.lua loaded.")
