; ImgBatch NSIS hooks — one parent menu + submenu via Explorer CommandStore.
; (SubCommands="" nested under Classes\...\shell is empty on Windows 11 modern menu.)
; SHCTX follows per-user / per-machine install mode.

!macro ImgBatchWriteStore ACTION LABEL PLACEHOLDER
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.${ACTION}" "MUIVerb" "${LABEL}"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.${ACTION}" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.${ACTION}" "MultiSelectModel" "Document"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.${ACTION}\command" "" '"$INSTDIR\imgbatch.exe" --quick ${ACTION} ${PLACEHOLDER}'
!macroend

!macro ImgBatchWriteParent ROOT
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch" "MUIVerb" "ImgBatch"
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch" "SubCommands" "ImgBatch.compress;ImgBatch.convert;ImgBatch.rename;ImgBatch.watermark;ImgBatch.trim;ImgBatch.normalize;ImgBatch.inspect"
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
  ; legacy file/folder-specific store ids (if any)
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.f.compress"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.d.compress"
!macroend

; Stop one process: silent kill with retries, then Tauri prompt if still running.
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
      Goto stop_done_${ImgBatchStopUid}
    ${EndIf}
    !if "${INSTALLMODE}" == "currentUser"
      nsis_tauri_utils::KillProcessCurrentUser "${executableName}"
    !else
      nsis_tauri_utils::KillProcess "${executableName}"
    !endif
    Pop $R0
    Sleep 800
    IntOp $R4 $R4 + 1
    ${If} $R4 < 5
      Goto stop_retry_${ImgBatchStopUid}
    ${EndIf}
  stop_done_${ImgBatchStopUid}:
  !undef ImgBatchStopUid
!macroend

!macro ImgBatchKillRunning
  ; Sidecar is not covered by Tauri's default CheckIfAppIsRunning (main exe only).
  !insertmacro ImgBatchStopProcess "imgbatch-api.exe"
  !insertmacro ImgBatchStopProcess "imgbatch.exe"
  !insertmacro CheckIfAppIsRunning "imgbatch-api.exe" "${PRODUCTNAME}"
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro ImgBatchKillRunning
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro ImgBatchKillRunning
!macroend

!macro NSIS_HOOK_POSTINSTALL
  ; Remove flat verbs / old cascades from previous builds
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

  ; CommandStore entries for files (%1) — used by * and image associations
  !insertmacro ImgBatchWriteStore "compress" "压缩" "%*"
  !insertmacro ImgBatchWriteStore "convert" "格式转换" "%*"
  !insertmacro ImgBatchWriteStore "rename" "重命名" "%*"
  !insertmacro ImgBatchWriteStore "watermark" "水印" "%*"
  !insertmacro ImgBatchWriteStore "trim" "裁边" "%*"
  !insertmacro ImgBatchWriteStore "normalize" "规范化" "%*"
  !insertmacro ImgBatchWriteStore "inspect" "检查" "%*"

  ; Parent menus: one "ImgBatch" entry with submenu
  !insertmacro ImgBatchWriteParent "*"
  !insertmacro ImgBatchWriteParent "Directory"
  !insertmacro ImgBatchWriteParent "Directory\Background"

  ; Folder parents need %V — override store commands for directory use via separate store ids
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.compress" "MUIVerb" "压缩"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.compress" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.compress\command" "" '"$INSTDIR\imgbatch.exe" --quick compress "%V"'
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert" "MUIVerb" "格式转换"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert\command" "" '"$INSTDIR\imgbatch.exe" --quick convert "%V"'
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.rename" "MUIVerb" "重命名"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.rename" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.rename\command" "" '"$INSTDIR\imgbatch.exe" --quick rename "%V"'
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.watermark" "MUIVerb" "水印"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.watermark" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.watermark\command" "" '"$INSTDIR\imgbatch.exe" --quick watermark "%V"'
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.trim" "MUIVerb" "裁边"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.trim" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.trim\command" "" '"$INSTDIR\imgbatch.exe" --quick trim "%V"'
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.normalize" "MUIVerb" "规范化"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.normalize" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.normalize\command" "" '"$INSTDIR\imgbatch.exe" --quick normalize "%V"'
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.inspect" "MUIVerb" "检查"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.inspect" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.inspect\command" "" '"$INSTDIR\imgbatch.exe" --quick inspect "%V"'

  WriteRegStr SHCTX "Software\Classes\Directory\shell\ImgBatch" "SubCommands" "ImgBatch.dir.compress;ImgBatch.dir.convert;ImgBatch.dir.rename;ImgBatch.dir.watermark;ImgBatch.dir.trim;ImgBatch.dir.normalize;ImgBatch.dir.inspect"
  WriteRegStr SHCTX "Software\Classes\Directory\Background\shell\ImgBatch" "SubCommands" "ImgBatch.dir.compress;ImgBatch.dir.convert;ImgBatch.dir.rename;ImgBatch.dir.watermark;ImgBatch.dir.trim;ImgBatch.dir.normalize;ImgBatch.dir.inspect"
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
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.compress"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.rename"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.watermark"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.trim"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.normalize"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.inspect"
!macroend
