-- JobRunner.lua
--
-- Handles the processing of a single development job.

local LrLogger = import 'LrLogger'
local LrDevelopController = import 'LrDevelopController'
local JSON = require 'Utils.JSON' -- Use 'require' to load modules from the plugin folder

local log = LrLogger('JunmaiAutoDevJobRunner')
log:enable("logfile")

local JobRunner = {}

---
-- Processes a single development job received from the API.
-- @param config (table) The decoded Lua table representing the job config.
-- @return (boolean) True if the job was processed successfully, false otherwise.
--
function JobRunner.runJob(config)
    log:info("JobRunner.runJob started.")

    if not config or type(config) ~= "table" then
        log:error("Invalid config table passed to JobRunner.")
        return false
    end

    log:info("Successfully decoded job JSON. Version: " .. tostring(config.version))

    -- 2. Get the active photo to apply settings to.
    -- Note: This requires the user to have a photo selected in the Develop module.
    local photo = LrDevelopController.getActivePhoto()
    if photo == nil then
        log:error("No active photo selected in the Develop module.")
        return false
    end

    log:info("Processing job for photo: " .. tostring(photo))

    -- 3. Iterate through the pipeline and apply settings for each stage
    if config.pipeline and type(config.pipeline) == "table" then
        for _, task in ipairs(config.pipeline) do
            local stage = task.stage
            log:info("--> Processing stage: " .. stage)

            if stage == "base" then
                if task.settings and type(task.settings) == "table" then
                    for key, value in pairs(task.settings) do
                        -- Handle special case for White Balance
                        if key == "WB" and type(value) == "table" then
                            local wb_ok, wb_err = pcall(LrDevelopController.setWhiteBalance, value.mode, { temp = value.temp, tint = value.tint })
                            if not wb_ok then
                                log:error(string.format("   Failed to set White Balance: %s", wb_err))
                            else
                                log:info(string.format("   Set WB to %s, Temp: %d, Tint: %d", value.mode, value.temp, value.tint))
                            end
                        else
                            -- Apply general settings
                            local ok, err = pcall(LrDevelopController.setValue, key, value)
                            if not ok then
                                log:error(string.format("   Failed to set '%s' to '%s': %s", key, tostring(value), err))
                            else
                                log:info(string.format("   Set '%s' to %s", key, tostring(value)))
                            end
                        end
                    end
                else
                    log:warn("   'base' stage is missing or has invalid 'settings' table.")
                end
            elseif stage == "toneCurve" then
                if task.rgb and type(task.rgb) == "table" then
                    local ok, err = pcall(LrDevelopController.setToneCurve, "rgb", task.rgb)
                    if not ok then
                        log:error(string.format("   Failed to set RGB tone curve: %s", err))
                    else
                        log:info("   Successfully set RGB tone curve.")
                    end
                else
                    log:warn("   'toneCurve' stage is missing or has invalid 'rgb' table.")
                end
            elseif stage == "HSL" then
                -- Helper function to apply HSL settings for a given type (hue, sat, lum)
                local function applyHslSettings(settingsTable, typeSuffix)
                    if settingsTable and type(settingsTable) == "table" then
                        for color, value in pairs(settingsTable) do
                            -- Capitalize the color name (e.g., "orange" -> "Orange")
                            local capitalizedColor = string.upper(string.sub(color, 1, 1)) .. string.sub(color, 2)
                            local settingName = capitalizedColor .. typeSuffix

                            local ok, err = pcall(LrDevelopController.setValue, settingName, value)
                            if not ok then
                                log:error(string.format("   Failed to set '%s' to '%s': %s", settingName, tostring(value), err))
                            else
                                log:info(string.format("   Set '%s' to %s", settingName, tostring(value)))
                            end
                        end
                    end
                end

                applyHslSettings(task.hue, "Hue")
                applyHslSettings(task.sat, "Saturation")
                applyHslSettings(task.lum, "Luminance")
            else
                log:warn("   Unknown or unsupported stage: " .. stage)
            end
        end
    else
        log:error("Job has no valid 'pipeline' array.")
        return false
    end

    log:info("Finished processing all stages for the job.")
    return true
end

return JobRunner
