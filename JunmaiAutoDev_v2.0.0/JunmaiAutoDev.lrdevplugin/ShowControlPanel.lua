-- ShowControlPanel.lua
--
-- Displays a reactive control panel for the Junmai Auto Develop plugin.

local LrDialogs = import 'LrDialogs'
local LrView = import 'LrView'
local LrBinding = import 'LrBinding'
local LrTasks = import 'LrTasks'

local Main = require 'Main'

LrTasks.startAsyncTask(function()

    local f = LrView.osFactory()

    -- Create a property table to bind UI elements to.
    local properties = LrBinding.makePropertyTable({})
    properties.status = Main.getStatus() -- Set the initial status

    -- Define the listener function that will update the UI.
    local function statusListener(newStatus)
        -- This needs to run on the main thread to update the UI safely.
        LrTasks.executeToPIMainThread(function()
            properties.status = newStatus
        end)
    end

    -- Add the listener to the main module.
    Main.addStatusListener(statusListener)

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

    -- Show the modal dialog. Execution will pause here until it's dismissed.
    local result = LrDialogs.presentModalDialog {
        title = "Junmai AutoDev Control Panel",
        contents = c,
        accessoryView = f:push_button {
            title = "Check for Job Now",
            action = function()
                -- Manually trigger a poll. The status will update automatically.
                Main.pollForNextJob()
            end,
        },
        -- We can't provide a custom action for the default "OK" or "Cancel".
        -- Instead, we must clean up the listener after the dialog closes.
        okButton = { title = "Close" },
    }

    -- After the dialog is closed (either by "Close" or the window 'X'),
    -- this code will execute. We remove the listener here to prevent memory leaks.
    Main.removeStatusListener(statusListener)

end)
