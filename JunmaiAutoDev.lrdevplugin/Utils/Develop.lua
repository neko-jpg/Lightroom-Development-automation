-- Utils/Develop.lua
--
-- Utility functions for finding and applying develop settings.

local LrApplication = import 'LrApplication'
local LrLogger = import 'LrLogger'

local log = LrLogger('JunmaiAutoDevDevelopUtils')
log:enable("logfile")

local DevelopUtils = {}

---
-- Recursively searches for a develop preset by its name.
-- @param presetName (string) The exact name of the preset to find.
-- @return (LrDevelopPreset) The preset object, or nil if not found.
--
function DevelopUtils.findPresetByName(presetName)
    log:info("Searching for preset: " .. presetName)

    local presetFolders = LrApplication.developPresetFolders()

    -- We need a local function for recursion
    local function searchInFolders(folders)
        for _, folder in ipairs(folders) do
            -- Search presets in the current folder
            local presets = folder:getDevelopPresets()
            for _, preset in ipairs(presets) do
                if preset:getName() == presetName then
                    log:info("Found preset '" .. presetName .. "'")
                    return preset
                end
            end

            -- Search in subfolders
            local subFolders = folder:getChildFolders()
            if #subFolders > 0 then
                local foundPreset = searchInFolders(subFolders)
                if foundPreset then
                    return foundPreset
                end
            end
        end
        return nil -- Not found in this branch
    end

    local found = searchInFolders(presetFolders)
    if not found then
        log:warn("Preset '" .. presetName .. "' not found in any folder.")
    end

    return found
end

return DevelopUtils
