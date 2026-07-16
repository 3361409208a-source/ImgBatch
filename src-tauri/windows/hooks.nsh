; ImgBatch NSIS hooks — cascading Explorer quick-action menus (not default open).
; SHCTX follows per-user / per-machine install mode.
; PLACEHOLDER is %1 for files or %V for directories (no extra quotes in the macro arg).

!macro ImgBatchWriteAction ROOT ACTION LABEL PLACEHOLDER
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch\shell\${ACTION}" "MUIVerb" "${LABEL}"
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch\shell\${ACTION}" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch\shell\${ACTION}" "MultiSelectModel" "Player"
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch\shell\${ACTION}\command" "" '"$INSTDIR\imgbatch.exe" --quick ${ACTION} "${PLACEHOLDER}"'
!macroend

!macro ImgBatchRegisterCascade ROOT PLACEHOLDER
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch" "MUIVerb" "ImgBatch"
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Classes\${ROOT}\shell\ImgBatch" "SubCommands" ""

  !insertmacro ImgBatchWriteAction "${ROOT}" "compress" "压缩" "${PLACEHOLDER}"
  !insertmacro ImgBatchWriteAction "${ROOT}" "convert" "格式转换" "${PLACEHOLDER}"
  !insertmacro ImgBatchWriteAction "${ROOT}" "rename" "重命名" "${PLACEHOLDER}"
  !insertmacro ImgBatchWriteAction "${ROOT}" "watermark" "水印" "${PLACEHOLDER}"
  !insertmacro ImgBatchWriteAction "${ROOT}" "trim" "裁边" "${PLACEHOLDER}"
  !insertmacro ImgBatchWriteAction "${ROOT}" "normalize" "规范化" "${PLACEHOLDER}"
  !insertmacro ImgBatchWriteAction "${ROOT}" "inspect" "检查" "${PLACEHOLDER}"
!macroend

!macro NSIS_HOOK_POSTINSTALL
  !insertmacro ImgBatchRegisterCascade "*" "%1"
  !insertmacro ImgBatchRegisterCascade "Directory" "%V"
  !insertmacro ImgBatchRegisterCascade "Directory\Background" "%V"
  !insertmacro ImgBatchRegisterCascade ".png" "%1"
  !insertmacro ImgBatchRegisterCascade ".jpg" "%1"
  !insertmacro ImgBatchRegisterCascade ".jpeg" "%1"
  !insertmacro ImgBatchRegisterCascade ".webp" "%1"
  !insertmacro ImgBatchRegisterCascade ".gif" "%1"
  !insertmacro ImgBatchRegisterCascade ".bmp" "%1"
  !insertmacro ImgBatchRegisterCascade ".tif" "%1"
  !insertmacro ImgBatchRegisterCascade ".tiff" "%1"
  !insertmacro ImgBatchRegisterCascade ".ico" "%1"
  !insertmacro ImgBatchRegisterCascade "SystemFileAssociations\image" "%1"
!macroend

!macro NSIS_HOOK_POSTUNINSTALL
  DeleteRegKey SHCTX "Software\Classes\*\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\Directory\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\Directory\Background\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\.png\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\.jpg\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\.jpeg\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\.webp\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\.gif\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\.bmp\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\.tif\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\.tiff\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\.ico\shell\ImgBatch"
  DeleteRegKey SHCTX "Software\Classes\SystemFileAssociations\image\shell\ImgBatch"
!macroend
