; setup.nsi
; Junmai AutoDev NSIS Installer Script (Final Version for Distribution Kit)

;--------------------------------
; Includes
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

;--------------------------------
; Product Information
!define PRODUCT_NAME "Junmai AutoDev"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Junmai Systems"
!define SETUP_EXE_NAME "JunmaiAutoDev_setup.exe"
!define LRPLUGIN_NAME "JunmaiAutoDev.lrdevplugin"
!define APP_EXE_NAME "JunmaiAutoDev.exe"

;--------------------------------
; MUI Settings
!define MUI_ABORTWARNING
;!define MUI_ICON "gui_qt/resources/icons/app_icon.ico" ; User should provide this

;--------------------------------
; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TEXT "Junmai AutoDev のインストールが完了しました。$\n$\nLightroom Classic を起動している場合は、一度再起動してください。"
!define MUI_FINISHPAGE_LINK "アプリケーションの使い方はこちら"
!define MUI_FINISHPAGE_LINK_LOCATION "https://github.com/your-repo/junmai-autodev/blob/main/README.md"
!insertmacro MUI_PAGE_FINISH

;--------------------------------
; Uninstaller Pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
; Language
!insertmacro MUI_LANGUAGE "Japanese"

;--------------------------------
; Installer Attributes
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "${SETUP_EXE_NAME}"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
RequestExecutionLevel admin
ShowInstDetails show

;--------------------------------
; Main Installer Section
Section "Junmai AutoDev Core" SEC_CORE
  SetOutPath $INSTDIR

  DetailPrint "アプリケーションファイルをインストールしています..."
  ; Recursively add all files from the packaged app directory
  File /r "dist\JunmaiAutoDev\"

  DetailPrint "AIエンジン (Ollama) をダウンロードしています..."
  NSISdl::download "https://ollama.com/download/windows" "$TEMP\OllamaSetup.exe"
  Pop $R0 ; Get the download result
  ${If} $R0 != "success"
    MessageBox MB_OK "Ollamaのダウンロードに失敗しました。インターネット接続を確認して、再度お試しください。"
    Abort
  ${EndIf}

  DetailPrint "AIエンジン (Ollama) をインストールしています... (これには数分かかる場合があります)"
  ExecWait '"$TEMP\OllamaSetup.exe" /S'

  DetailPrint "Lightroomプラグインをインストールしています..."
  StrCpy $R0 "$APPDATA\Adobe\Lightroom\Modules"
  IfFileExists "$R0" 0 +2
    GoTo copy_plugin

  CreateDirectory "$R0"

  copy_plugin:
  SetOutPath "$R0\${LRPLUGIN_NAME}"
  File /r "${LRPLUGIN_NAME}\*"

  SetOutPath $INSTDIR
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${APP_EXE_NAME}"

  WriteUninstaller "$INSTDIR\uninstall.exe"

  DetailPrint "インストールが完了しました。"
SectionEnd

;--------------------------------
; Uninstaller Section
Section "Uninstall"
  ; Remove application directory
  RMDir /r "$INSTDIR"

  ; Remove Lightroom plugin
  RMDir /r "$APPDATA\Adobe\Lightroom\Modules\${LRPLUGIN_NAME}"

  ; Remove shortcut
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
SectionEnd
