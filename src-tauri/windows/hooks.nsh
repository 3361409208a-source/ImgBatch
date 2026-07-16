; ImgBatch NSIS hooks — parent menu + submenus via Explorer CommandStore.
; SHCTX follows per-user / per-machine install mode.

!macro ImgBatchWriteQuickVerb STORE_ID LABEL QUICK_ARGS PLACEHOLDER
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "MUIVerb" "${LABEL}"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "MultiSelectModel" "Player"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}\command" "" '"$INSTDIR\imgbatch.exe" --quick ${QUICK_ARGS} "${PLACEHOLDER}"'
!macroend

!macro ImgBatchWriteConvertVerb STORE_ID LABEL FMT PLACEHOLDER
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "MUIVerb" "${LABEL}"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "Icon" "$INSTDIR\imgbatch.exe,0"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}" "MultiSelectModel" "Player"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\${STORE_ID}\command" "" '"$INSTDIR\imgbatch.exe" --quick convert --format ${FMT} --auto-run "${PLACEHOLDER}"'
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
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchMore"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchSep"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchCompress"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchConvert"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchRename"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchWatermark"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchTrim"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchNormalize"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchInspect"
  DeleteRegKey SHCTX "Software\Classes\${ROOT}\shell\ImgBatchGif"
!macroend

!macro ImgBatchDeleteStore
  ; compress
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.compress"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.compress.high"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.compress.standard"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.compress.max"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.compress.thumb"
  ; convert
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.png"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.jpg"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.webp"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.bmp"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.tiff"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.gif"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.ico"
  ; rename
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.rename"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.rename.prefix"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.rename.lower"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.rename.upper"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.rename.suffix"
  ; watermark
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.watermark"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.watermark.br"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.watermark.center"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.watermark.tl"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.watermark.copy"
  ; trim
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.trim"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.trim.p0"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.trim.p4"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.trim.p8"
  ; normalize
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.normalize"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.normalize.h280"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.normalize.h512"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.normalize.h1024"
  ; inspect
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.inspect"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.inspect.quick"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.inspect.open"
  ; gif
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif.optimize"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif.resize50"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif.resize75"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif.colors"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif.speed2"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif.speed05"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif.reverse"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif.trim"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif.wm"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.gif.extract"

  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.misc"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.more"
!macroend

!macro ImgBatchDeleteDirStore
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.compress"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.compress.high"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.compress.standard"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.compress.max"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.compress.thumb"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.png"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.jpg"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.webp"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.bmp"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.tiff"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.gif"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.ico"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.rename"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.rename.prefix"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.rename.lower"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.rename.upper"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.rename.suffix"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.watermark"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.watermark.br"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.watermark.center"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.watermark.tl"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.watermark.copy"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.trim"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.trim.p0"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.trim.p4"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.trim.p8"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.normalize"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.normalize.h280"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.normalize.h512"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.normalize.h1024"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.inspect"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.inspect.quick"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.inspect.open"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif.optimize"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif.resize50"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif.resize75"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif.colors"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif.speed2"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif.speed05"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif.reverse"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif.trim"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif.wm"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.gif.extract"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.misc"
  DeleteRegKey SHCTX "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.more"
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
    ExecWait 'taskkill /F /IM "${executableName}" /T' $R0
    Sleep 1200
  stop_done_${ImgBatchStopUid}:
  !undef ImgBatchStopUid
!macroend

!macro ImgBatchKillRunning
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

  ; ── Compress ──
  !insertmacro ImgBatchWriteParent "ImgBatch.compress" "压缩" "ImgBatch.compress.high;ImgBatch.compress.standard;ImgBatch.compress.max;ImgBatch.compress.thumb"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.compress.high" "高画质 (90)" "compress --quality 90 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.compress.standard" "标准 (75)" "compress --quality 75 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.compress.max" "极限压缩 (50)" "compress --quality 50 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.compress.thumb" "缩略图 50%" "compress --quality 50 --resize 50 --auto-run" "%1"
  !insertmacro ImgBatchWriteParent "ImgBatch.dir.compress" "压缩" "ImgBatch.dir.compress.high;ImgBatch.dir.compress.standard;ImgBatch.dir.compress.max;ImgBatch.dir.compress.thumb"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.compress.high" "高画质 (90)" "compress --quality 90 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.compress.standard" "标准 (75)" "compress --quality 75 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.compress.max" "极限压缩 (50)" "compress --quality 50 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.compress.thumb" "缩略图 50%" "compress --quality 50 --resize 50 --auto-run" "%V"

  ; ── Convert ──
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

  ; ── Rename ──
  !insertmacro ImgBatchWriteParent "ImgBatch.rename" "重命名" "ImgBatch.rename.prefix;ImgBatch.rename.lower;ImgBatch.rename.upper;ImgBatch.rename.suffix"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.rename.prefix" "序号前缀" "rename --rename-mode prefix --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.rename.lower" "转小写" "rename --rename-mode lowercase --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.rename.upper" "转大写" "rename --rename-mode uppercase --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.rename.suffix" "添加后缀 _bak" "rename --rename-mode suffix --auto-run" "%1"
  !insertmacro ImgBatchWriteParent "ImgBatch.dir.rename" "重命名" "ImgBatch.dir.rename.prefix;ImgBatch.dir.rename.lower;ImgBatch.dir.rename.upper;ImgBatch.dir.rename.suffix"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.rename.prefix" "序号前缀" "rename --rename-mode prefix --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.rename.lower" "转小写" "rename --rename-mode lowercase --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.rename.upper" "转大写" "rename --rename-mode uppercase --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.rename.suffix" "添加后缀 _bak" "rename --rename-mode suffix --auto-run" "%V"

  ; ── Watermark ──
  !insertmacro ImgBatchWriteParent "ImgBatch.watermark" "水印" "ImgBatch.watermark.br;ImgBatch.watermark.center;ImgBatch.watermark.tl;ImgBatch.watermark.copy"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.watermark.br" "右下水印" "watermark --wm-position bottom-right --wm-text ImgBatch --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.watermark.center" "居中水印" "watermark --wm-position center --wm-text ImgBatch --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.watermark.tl" "左上水印" "watermark --wm-position top-left --wm-text ImgBatch --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.watermark.copy" "版权 ©" "watermark --wm-position bottom-right --wm-text ImgBatch --auto-run" "%1"
  !insertmacro ImgBatchWriteParent "ImgBatch.dir.watermark" "水印" "ImgBatch.dir.watermark.br;ImgBatch.dir.watermark.center;ImgBatch.dir.watermark.tl;ImgBatch.dir.watermark.copy"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.watermark.br" "右下水印" "watermark --wm-position bottom-right --wm-text ImgBatch --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.watermark.center" "居中水印" "watermark --wm-position center --wm-text ImgBatch --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.watermark.tl" "左上水印" "watermark --wm-position top-left --wm-text ImgBatch --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.watermark.copy" "版权 ©" "watermark --wm-position bottom-right --wm-text ImgBatch --auto-run" "%V"

  ; ── Trim ──
  !insertmacro ImgBatchWriteParent "ImgBatch.trim" "裁边" "ImgBatch.trim.p0;ImgBatch.trim.p4;ImgBatch.trim.p8"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.trim.p0" "无边距" "trim --padding 0 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.trim.p4" "标准 4px" "trim --padding 4 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.trim.p8" "宽边距 8px" "trim --padding 8 --auto-run" "%1"
  !insertmacro ImgBatchWriteParent "ImgBatch.dir.trim" "裁边" "ImgBatch.dir.trim.p0;ImgBatch.dir.trim.p4;ImgBatch.dir.trim.p8"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.trim.p0" "无边距" "trim --padding 0 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.trim.p4" "标准 4px" "trim --padding 4 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.trim.p8" "宽边距 8px" "trim --padding 8 --auto-run" "%V"

  ; ── Normalize ──
  !insertmacro ImgBatchWriteParent "ImgBatch.normalize" "规范化" "ImgBatch.normalize.h280;ImgBatch.normalize.h512;ImgBatch.normalize.h1024"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.normalize.h280" "高度 280" "normalize --target-height 280 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.normalize.h512" "高度 512" "normalize --target-height 512 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.normalize.h1024" "高度 1024" "normalize --target-height 1024 --auto-run" "%1"
  !insertmacro ImgBatchWriteParent "ImgBatch.dir.normalize" "规范化" "ImgBatch.dir.normalize.h280;ImgBatch.dir.normalize.h512;ImgBatch.dir.normalize.h1024"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.normalize.h280" "高度 280" "normalize --target-height 280 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.normalize.h512" "高度 512" "normalize --target-height 512 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.normalize.h1024" "高度 1024" "normalize --target-height 1024 --auto-run" "%V"

  ; ── Inspect ──
  !insertmacro ImgBatchWriteParent "ImgBatch.inspect" "检查" "ImgBatch.inspect.quick;ImgBatch.inspect.open"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.inspect.quick" "快速检查 PNG" "inspect --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.inspect.open" "打开检查面板" "inspect" "%1"
  !insertmacro ImgBatchWriteParent "ImgBatch.dir.inspect" "检查" "ImgBatch.dir.inspect.quick;ImgBatch.dir.inspect.open"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.inspect.quick" "快速检查 PNG" "inspect --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.inspect.open" "打开检查面板" "inspect" "%V"

  ; ── GIF ──
  !insertmacro ImgBatchWriteParent "ImgBatch.gif" "GIF 动图" "ImgBatch.gif.optimize;ImgBatch.gif.resize50;ImgBatch.gif.resize75;ImgBatch.gif.colors;ImgBatch.gif.speed2;ImgBatch.gif.speed05;ImgBatch.gif.reverse;ImgBatch.gif.trim;ImgBatch.gif.wm;ImgBatch.gif.extract"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.gif.optimize" "优化体积" "gif --gif-mode optimize --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.gif.resize50" "缩小 50%" "gif --gif-mode resize --resize 50 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.gif.resize75" "缩小 75%" "gif --gif-mode resize --resize 75 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.gif.colors" "减色 128" "gif --gif-mode reduce_colors --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.gif.speed2" "2倍速" "gif --gif-mode speed --speed 2 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.gif.speed05" "半速 0.5x" "gif --gif-mode speed --speed 0.5 --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.gif.reverse" "倒放" "gif --gif-mode reverse --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.gif.trim" "裁透明边" "gif --gif-mode trim --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.gif.wm" "加水印" "gif --gif-mode watermark --auto-run" "%1"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.gif.extract" "拆帧导出" "gif --gif-mode extract --auto-run" "%1"
  !insertmacro ImgBatchWriteParent "ImgBatch.dir.gif" "GIF 动图" "ImgBatch.dir.gif.optimize;ImgBatch.dir.gif.resize50;ImgBatch.dir.gif.resize75;ImgBatch.dir.gif.colors;ImgBatch.dir.gif.speed2;ImgBatch.dir.gif.speed05;ImgBatch.dir.gif.reverse;ImgBatch.dir.gif.trim;ImgBatch.dir.gif.wm;ImgBatch.dir.gif.extract"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.gif.optimize" "优化体积" "gif --gif-mode optimize --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.gif.resize50" "缩小 50%" "gif --gif-mode resize --resize 50 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.gif.resize75" "缩小 75%" "gif --gif-mode resize --resize 75 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.gif.colors" "减色 128" "gif --gif-mode reduce_colors --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.gif.speed2" "2倍速" "gif --gif-mode speed --speed 2 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.gif.speed05" "半速 0.5x" "gif --gif-mode speed --speed 0.5 --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.gif.reverse" "倒放" "gif --gif-mode reverse --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.gif.trim" "裁透明边" "gif --gif-mode trim --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.gif.wm" "加水印" "gif --gif-mode watermark --auto-run" "%V"
  !insertmacro ImgBatchWriteQuickVerb "ImgBatch.dir.gif.extract" "拆帧导出" "gif --gif-mode extract --auto-run" "%V"

  ; ── Misc flat group (trim / normalize / inspect / common GIF) ──
  !insertmacro ImgBatchWriteParent "ImgBatch.misc" "其他工具" "ImgBatch.trim.p0;ImgBatch.trim.p4;ImgBatch.trim.p8;ImgBatch.normalize.h280;ImgBatch.normalize.h512;ImgBatch.normalize.h1024;ImgBatch.inspect.quick;ImgBatch.inspect.open;ImgBatch.gif.optimize;ImgBatch.gif.resize50;ImgBatch.gif.reverse;ImgBatch.gif.extract"
  !insertmacro ImgBatchWriteParent "ImgBatch.dir.misc" "其他工具" "ImgBatch.dir.trim.p0;ImgBatch.dir.trim.p4;ImgBatch.dir.trim.p8;ImgBatch.dir.normalize.h280;ImgBatch.dir.normalize.h512;ImgBatch.dir.normalize.h1024;ImgBatch.dir.inspect.quick;ImgBatch.dir.inspect.open;ImgBatch.dir.gif.optimize;ImgBatch.dir.gif.resize50;ImgBatch.dir.gif.reverse;ImgBatch.dir.gif.extract"

  ; ── More submenu (rename / watermark / misc) ──
  !insertmacro ImgBatchWriteParent "ImgBatch.more" "更多" "ImgBatch.rename;ImgBatch.watermark;ImgBatch.misc"
  !insertmacro ImgBatchWriteParent "ImgBatch.dir.more" "更多" "ImgBatch.dir.rename;ImgBatch.dir.watermark;ImgBatch.dir.misc"

  ; ── Single top-level ImgBatch (Windows shows ~3 cascades) ──
  !insertmacro ImgBatchWriteClassParent "*" "ImgBatch.compress;ImgBatch.convert;ImgBatch.more"
  !insertmacro ImgBatchWriteClassParent "Directory" "ImgBatch.dir.compress;ImgBatch.dir.convert;ImgBatch.dir.more"
  !insertmacro ImgBatchWriteClassParent "Directory\Background" "ImgBatch.dir.compress;ImgBatch.dir.convert;ImgBatch.dir.more"
  !insertmacro ImgBatchWriteClassParent "SystemFileAssociations\image" "ImgBatch.compress;ImgBatch.convert;ImgBatch.more"
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
