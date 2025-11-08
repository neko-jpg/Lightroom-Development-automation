-- Info.lua
--
-- Lightroom plugin definition file for JunmaiAutoDev.

return {
    LrSdkVersion = 13.0,
    LrSdkMinimumVersion = 12.0, -- Requires Lightroom Classic 12.0 or later

    LrPluginName = "Junmai Auto Develop",
    LrPluginId = "com.junmai.lightroom.autodev",
    LrPluginVersion = "0.1.0",

    -- This plugin adds a menu item to the File > Plug-in Extras menu.
    -- This plugin adds a menu item to the Library > Plug-in Extras menu.
    LrLibraryMenuItems = {
        {
            title = "Junmai AutoDev Control Panel",
            file = "ShowControlPanel.lua",
        },
    },

    -- The main logic file, loaded when the plugin is enabled.
    "Main.lua",

    VERSION = { major=0, minor=1, revision=0, build=1, ZSTRING="0.1.0.1" },
}
