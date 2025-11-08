-- ShowControlPanel.lua
--
-- Displays a simple control panel for the Junmai Auto Develop plugin.

local LrDialogs = import 'LrDialogs'
local LrView = import 'LrView'
local LrBinding = import 'LrBinding'

-- We need to access the main module to get the status and trigger polling.
-- 'require' is used here to ensure we get the same instance of the module that Lightroom loaded.
local Main = require 'Main'

-- Show a simple modal dialog with the current status and a run button.
LrTasks.startAsyncTask(function()

    local f = LrView.osFactory()

    local properties = LrBinding.makePropertyTable({})
    properties.status = Main.getStatus() -- Get initial status

    -- Create a dialog box contents
    local c = f:column {
        bind_to_object = properties,
        spacing = f:control_spacing(),

        f:row {
            spacing = f:control_spacing(),
            f:static_text {
                title = "Plugin Status:",
                width = LrView.share "label",
            },
            f:static_text {
                title = bind "status",
                width = LrView.share "value",
            },
        },
    }

    -- Show the dialog
    local result = LrDialogs.presentModalDialog {
        title = "Junmai AutoDev Control Panel",
        contents = c,
        accessoryView = f:push_button {
            title = "Check for Job Now",
            action = function()
                Main.pollForNextJob()
                -- No easy way to refresh the dialog, but the next time it's opened, it will be updated.
                LrDialogs.dismissDialog(result)
            end,
        },
        cancelButton = { title = "Close" },
    }
end)
