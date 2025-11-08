-- JobRunner.lua
--
-- Handles the processing of a single development job.

local LrLogger = import 'LrLogger'
local LrDevelopController = import 'LrDevelopController'
local LrApplication = import 'LrApplication' -- Import LrApplication to get catalog access
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

    -- 1. Get the original photo to apply settings to.
    local originalPhoto = LrDevelopController.getActivePhoto()
    if originalPhoto == nil then
        log:error("No active photo selected in the Develop module.")
        return false
    end
    log:info("Original photo found: " .. tostring(originalPhoto))


    -- 2. Create a virtual copy and a snapshot for safety. This must be done inside a write-access task.
    local catalog = LrApplication.activeCatalog()
    local photoToEdit = nil -- This will hold our new virtual copy

    local actionName = "JunmaiAutoDev: Prepare Photo for Auto Development"
    local success, result = catalog:withWriteAccessDo(actionName, function()
        -- Set the current photo as the selection to create the virtual copy from it.
        catalog:setSelectedPhotos(originalPhoto)

        -- Create the virtual copy. The new copy becomes the active selection.
        local virtualCopies = catalog:createVirtualCopies("JunmaiAutoDev Edit")
        if virtualCopies and #virtualCopies > 0 then
            photoToEdit = virtualCopies[1]
            log:info("Successfully created virtual copy: " .. tostring(photoToEdit))

            -- Create a snapshot on the new virtual copy before applying changes
            local snapshotSuccess, snapshotError = photoToEdit:createDevelopSnapshot("JunmaiAutoDev - Before", false)
            if snapshotSuccess then
                log:info("Successfully created 'Before' snapshot on virtual copy.")
            else
                log:error("Failed to create snapshot: " .. tostring(snapshotError))
                -- Proceed even if snapshot fails, but log it.
            end
        else
            log:error("Failed to create a virtual copy.")
            return false -- Signal failure to the withWriteAccessDo block
        end
        return true -- Signal success
    end)

    if not success or not photoToEdit then
        log:error("Could not prepare photo with virtual copy and snapshot. Aborting job.")
        if type(result) == "string" then
            log:error("Reason: " .. result)
        end
        return false
    end

    -- After creation, the virtual copy should be the active photo.
    -- All subsequent LrDevelopController calls will apply to it.
    log:info("Processing job for virtual copy: " .. tostring(photoToEdit))

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
            elseif stage == "detail" then
                -- Sharpening
                if task.sharpen and type(task.sharpen) == "table" then
                    local sharpenMap = { amount = "SharpeningAmount", radius = "SharpeningRadius", detail = "SharpeningDetail", masking = "SharpeningMasking" }
                    for key, settingName in pairs(sharpenMap) do
                        if task.sharpen[key] ~= nil then
                            local ok, err = pcall(LrDevelopController.setValue, settingName, task.sharpen[key])
                            if not ok then log:error(string.format("   Failed to set '%s': %s", settingName, err)) else log:info(string.format("   Set '%s' to %s", settingName, tostring(task.sharpen[key]))) end
                        end
                    end
                end
                -- Noise Reduction
                if task.nr and type(task.nr) == "table" then
                    local nrMap = { luminance = "LuminanceNoiseReduction", color = "ColorNoiseReduction" }
                    for key, settingName in pairs(nrMap) do
                        if task.nr[key] ~= nil then
                           local ok, err = pcall(LrDevelopController.setValue, settingName, task.nr[key])
                           if not ok then log:error(string.format("   Failed to set '%s': %s", settingName, err)) else log:info(string.format("   Set '%s' to %s", settingName, tostring(task.nr[key]))) end
                        end
                    end
                end
            elseif stage == "effects" then
                -- Grain
                if task.grain and type(task.grain) == "table" and task.grain.amount ~= nil then
                    local ok, err = pcall(LrDevelopController.setValue, "GrainAmount", task.grain.amount)
                    if not ok then log:error(string.format("   Failed to set 'GrainAmount': %s", err)) else log:info(string.format("   Set 'GrainAmount' to %s", tostring(task.grain.amount))) end
                end
                -- Vignette
                if task.vignette and type(task.vignette) == "table" then
                    local vignetteMap = { amount = "PostCropVignetteAmount", midpoint = "PostCropVignetteMidpoint", roundness = "PostCropVignetteRoundness", feather = "PostCropVignetteFeather" }
                    for key, settingName in pairs(vignetteMap) do
                        if task.vignette[key] ~= nil then
                            local ok, err = pcall(LrDevelopController.setValue, settingName, task.vignette[key])
                            if not ok then log:error(string.format("   Failed to set '%s': %s", settingName, err)) else log:info(string.format("   Set '%s' to %s", settingName, tostring(task.vignette[key]))) end
                        end
                    end
                end
            elseif stage == "calibration" then
                local calibrationMap = {
                    redPrimary = { hue = "RedHue", sat = "RedSaturation" },
                    greenPrimary = { hue = "GreenHue", sat = "GreenSaturation" },
                    bluePrimary = { hue = "BlueHue", sat = "BlueSaturation" }
                }
                for primary, settings in pairs(calibrationMap) do
                    if task[primary] and type(task[primary]) == "table" then
                        for prop, settingName in pairs(settings) do
                            if task[primary][prop] ~= nil then
                                local value = task[primary][prop]
                                local ok, err = pcall(LrDevelopController.setValue, settingName, value)
                                if not ok then log:error(string.format("   Failed to set '%s': %s", settingName, err)) else log:info(string.format("   Set '%s' to %s", settingName, tostring(value))) end
                            end
                        end
                    end
                end
            elseif stage == "preset" then
                local DevelopUtils = require 'Utils.Develop'
                if task.apply and type(task.apply) == "table" then
                    for _, presetName in ipairs(task.apply) do
                        local preset = DevelopUtils.findPresetByName(presetName)
                        if preset then
                            log:info("   Applying preset: " .. presetName)

                            local baseSettingsToBlend = {
                                "Exposure", "Contrast", "Highlights", "Shadows", "Whites", "Blacks",
                                "Clarity", "Dehaze", "Vibrance", "Saturation"
                            }
                            local beforeValues = {}
                            local blendAmount = (task.blend and task.blend.amount) and (task.blend.amount / 100.0) or nil

                            if blendAmount then
                                log:info("   Blend amount found: " .. (blendAmount * 100) .. "%. Getting 'before' values.")
                                for _, setting in ipairs(baseSettingsToBlend) do
                                    beforeValues[setting] = LrDevelopController.getValue(setting)
                                end
                            end

                            local cat = LrApplication.activeCatalog()
                            local ok, err = cat:withWriteAccessDo("Apply Develop Preset", function()
                                photoToEdit:applyDevelopPreset(preset)
                            end)

                            if not ok then
                                log:error(string.format("   Failed to apply preset '%s': %s", presetName, tostring(err)))
                                goto continue_loop
                            else
                                log:info(string.format("   Successfully applied preset '%s'", presetName))
                            end

                            if blendAmount then
                                log:info("   Applying blend...")
                                for _, setting in ipairs(baseSettingsToBlend) do
                                    local beforeVal = beforeValues[setting]
                                    local afterVal = LrDevelopController.getValue(setting)
                                    if type(beforeVal) == 'number' and type(afterVal) == 'number' then
                                        local finalVal = beforeVal + (afterVal - beforeVal) * blendAmount
                                        local p_ok, p_err = pcall(LrDevelopController.setValue, setting, finalVal)
                                        if not p_ok then
                                            log:error(string.format("   Blend failed for '%s': %s", setting, p_err))
                                        else
                                            log:info(string.format("   Blended '%s' to %s", setting, tostring(finalVal)))
                                        end
                                    end
                                end
                            end
                        else
                            log:warn(string.format("   Preset '%s' not found.", presetName))
                        end
                        ::continue_loop::
                    end
                else
                    log:warn("   'preset' stage is missing or has invalid 'apply' table.")
                end
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
