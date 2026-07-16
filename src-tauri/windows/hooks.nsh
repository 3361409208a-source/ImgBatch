; ImgBatch NSIS hooks — one parent menu + submenu via Explorer CommandStore.
; (SubCommands="" nested under Classes\...\shell is empty on Windows 11 modern menu.)
; SHCTX follows per-user / per-machine install mode.

!macro ImgBatchWriteLeafVerb STORE_ID LABEL ACTION PLACEHOLDER
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "MUIVerb" "${LABEL}"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "MultiSelectModel" "Player"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}\command" "" '"$INSTDIR\imgbatch.exe" --quick ${ACTION} "${PLACEHOLDER}"'
!macroend

!macro ImgBatchWriteConvertVerb STORE_ID LABEL FMT PLACEHOLDER
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "MUIVerb" "${LABEL}"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "MultiSelectModel" "Player"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}\command" "" '"$INSTDIR\imgbatch.exe" --quick convert --format ${FMT} "${PLACEHOLDER}"'
!macroend

!macro ImgBatchWriteParent STORE_ID LABEL SUBCOMMANDS
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "MUIVerb" "${LABEL}"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "SubCommands" "${SUBCOMMANDS}"
!macroend

!macro ImgBatchWriteClassParent ROOT SUBCOMMANDS
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch" "MUIVerb" "ImgBatch"
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch" "SubCommands" "${SUBCOMMANDS}"
!macroend

!macro ImgBatchDeleteFlat ROOT
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchSep"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchCompress"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchConvert"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchRename"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchWatermark"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchTrim"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchNormalize"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchInspect"
!macroend

!macro ImgBatchDeleteStore
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.compress"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.rename"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.watermark"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.trim"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.normalize"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.inspect"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.png"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.jpg"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.webp"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.bmp"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.tiff"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.gif"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.ico"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.f.compress"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.d.compress"
!macroend

!macro ImgBatchDeleteDirStore
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.compress"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.rename"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.watermark"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.trim"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.normalize"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.inspect"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.png"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.jpg"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.webp"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.bmp"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.tiff"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.gif"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.ico"
!macroend

; Stop one process: silent kill with retries, then taskkill /T fallback.
!macro ImgBatchStopProcess executableName
  !define ImgBatchStopUid ${__LINE__}
  StrCpy $R4 0
  stop_retry_${ImgBatchStopUid}:
    !if "${INSTALLMODE}" == "currentUser"
      nsis_tauri_utils::FindProcessCurrentUser "${executableName}"
    !else
      nsis_tauri_utils::FindProcess "${executableName}"
    !endif
    Pop $R0
    ${If} $R0 <> 0
      Goto stop_taskkill_${ImgBatchStopUid}
    ${EndIf}
    !if "${INSTALLMODE}" == "currentUser"
      nsis_tauri_utils::KillProcessCurrentUser "${executableName}"
    !else
      nsis_tauri_utils::KillProcess "${executableName}"
    !endif
    Pop $R0
    Sleep 1000
    IntOp $R4 $R4 + 1
    ${If} $R4 < 8
      Goto stop_retry_${ImgBatchStopUid}
    ${EndIf}
  stop_taskkill_${ImgBatchStopUid}:
    ; /T kills child processes (sidecar) — exit 128 when already gone is fine
    ExecWait 'taskkill /F /IM "${executableName}" /T' $R0
    Sleep 1200
  stop_done_${ImgBatchStopUid}:
  !undef ImgBatchStopUid
!macroend

!macro ImgBatchKillRunning
  ; Kill UI first so it cannot respawn imgbatch-api.exe, then kill sidecar.
  !insertmacro ImgBatchStopProcess "imgbatch.exe"
  Sleep 1500
  !insertmacro ImgBatchStopProcess "imgbatch-api.exe"
  Sleep 1500
  !insertmacro CheckIfAppIsRunning "imgbatch.exe" "${PRODUCTNAME}"
  !insertmacro CheckIfAppIsRunning "imgbatch-api.exe" "${PRODUCTNAME}"
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro ImgBatchKillRunning
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro ImgBatchKillRunning
!macroend

!macro NSIS_HOOK_POSTINSTALL
  !insertmacro ImgBatchDeleteFlat "*"
  !insertmacro ImgBatchDeleteFlat "Directory"
  !insertmacro ImgBatchDeleteFlat "Directory\Background"
  !insertmacro ImgBatchDeleteFlat ".png"
  !insertmacro ImgBatchDeleteFlat ".jpg"
  !insertmacro ImgBatchDeleteFlat ".jpeg"
  !insertmacro ImgBatchDeleteFlat ".webp"
  !insertmacro ImgBatchDeleteFlat ".gif"
  !insertmacro ImgBatchDeleteFlat ".bmp"
  !insertmacro ImgBatchDeleteFlat ".tif"
  !insertmacro ImgBatchDeleteFlat ".tiff"
  !insertmacro ImgBatchDeleteFlat ".ico"
  !insertmacro ImgBatchDeleteFlat "SystemFileAssociations\image"
  !insertmacro ImgBatchDeleteStore
  !insertmacro ImgBatchDeleteDirStore

  ; Leaf verbs for files (%1) and folders (%V)
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.compress" "压缩" "compress" "%1"
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.rename" "重命名" "rename" "%1"
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.watermark" "水印" "watermark" "%1"
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.trim" "裁边" "trim" "%1"
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.normalize" "规范化" "normalize" "%1"
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.inspect" "检查" "inspect" "%1"

  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.dir.compress" "压缩" "compress" "%V"
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.dir.rename" "重命名" "rename" "%V"
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.dir.watermark" "水印" "watermark" "%V"
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.dir.trim" "裁边" "trim" "%V"
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.dir.normalize" "规范化" "normalize" "%V"
  !insertmacro ImgBatchWriteLeafVerb "ImgBatch.dir.inspect" "检查" "inspect" "%V"

  ; Convert format submenu
  !insertmacro ImgBatchWriteParent "ImgBatch.convert" "格式转换" "ImgBatch.convert.png;ImgBatch.convert.jpg;ImgBatch.convert.webp;ImgBatch.convert.bmp;ImgBatch.convert.tiff;ImgBatch.convert.gif;ImgBatch.convert.ico"
  !insertmacro ImgBatchWriteParent "ImgBatch.dir.convert" "格式转换" "ImgBatch.dir.convert.png;ImgBatch.dir.convert.jpg;ImgBatch.dir.convert.webp;ImgBatch.dir.convert.bmp;ImgBatch.dir.convert.tiff;ImgBatch.dir.convert.gif;ImgBatch.dir.convert.ico"

  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.convert.png" "转为 PNG" ".png" "%1"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.convert.jpg" "转为 JPG" ".jpg" "%1"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.convert.webp" "转为 WEBP" ".webp" "%1"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.convert.bmp" "转为 BMP" ".bmp" "%1"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.convert.tiff" "转为 TIFF" ".tiff" "%1"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.convert.gif" "转为 GIF" ".gif" "%1"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.convert.ico" "转为 ICO" ".ico" "%1"

  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.dir.convert.png" "转为 PNG" ".png" "%V"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.dir.convert.jpg" "转为 JPG" ".jpg" "%V"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.dir.convert.webp" "转为 WEBP" ".webp" "%V"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.dir.convert.bmp" "转为 BMP" ".bmp" "%V"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.dir.convert.tiff" "转为 TIFF" ".tiff" "%V"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.dir.convert.gif" "转为 GIF" ".gif" "%V"
  !insertmacro ImgBatchWriteConvertVerb "ImgBatch.dir.convert.ico" "转为 ICO" ".ico" "%V"

  ; Parent menus on file / folder classes
  !insertmacro ImgBatchWriteClassParent "*" "ImgBatch.compress;ImgBatch.convert;ImgBatch.rename;ImgBatch.watermark;ImgBatch.trim;ImgBatch.normalize;ImgBatch.inspect"
  !insertmacro ImgBatchWriteClassParent "Directory" "ImgBatch.dir.compress;ImgBatch.dir.convert;ImgBatch.dir.rename;ImgBatch.dir.watermark;ImgBatch.dir.trim;ImgBatch.dir.normalize;ImgBatch.dir.inspect"
  !insertmacro ImgBatchWriteClassParent "Directory\Background" "ImgBatch.dir.compress;ImgBatch.dir.convert;ImgBatch.dir.rename;ImgBatch.dir.watermark;ImgBatch.dir.trim;ImgBatch.dir.normalize;ImgBatch.dir.inspect"
!macroend

!macro NSIS_HOOK_POSTUNINSTALL
  !insertmacro ImgBatchDeleteFlat "*"
  !insertmacro ImgBatchDeleteFlat "Directory"
  !insertmacro ImgBatchDeleteFlat "Directory\Background"
  !insertmacro ImgBatchDeleteFlat ".png"
  !insertmacro ImgBatchDeleteFlat ".jpg"
  !insertmacro ImgBatchDeleteFlat ".jpeg"
  !insertmacro ImgBatchDeleteFlat ".webp"
  !insertmacro ImgBatchDeleteFlat ".gif"
  !insertmacro ImgBatchDeleteFlat ".bmp"
  !insertmacro ImgBatchDeleteFlat ".tif"
  !insertmacro ImgBatchDeleteFlat ".tiff"
  !insertmacro ImgBatchDeleteFlat ".ico"
  !insertmacro ImgBatchDeleteFlat "SystemFileAssociations\image"
  !insertmacro ImgBatchDeleteStore
  !insertmacro ImgBatchDeleteDirStore
!macroend
