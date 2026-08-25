RUNTIME-UPDATE — files changed by opencode (2026-08-25)
=========================================================

Copy each file back into the project at the SAME relative path
(the folder structure here mirrors the project root).

WHAT CHANGED / WHY
------------------
1) FIX Box64 "waiting for guest render" (no presents):
   runtime/patches/box64-vulkan-dispatch-tile-qcom.patch
   + added wrappers: vkQueueSetPerfHintQCOM (iFpp),
     vkGetPhysicalDeviceQueuePerfHintPropertiesQCOM (vFpp)

2) FIX FEX SIGABRT "munmap_chunk(): invalid pointer":
   runtime/patches/bachata-libcinternal-fclose-guard.patch  (NEW)
   runtime/sources/shadps4/src/core/libraries/libc_internal/libc_internal_io.cpp
   + ownership guard: foreign FILE* from real sce_module libc is no
     longer free()'d; double-close safe; _Buf free guarded.

3) Vortek removed / optional:
   runtime/scripts/package-runtime.mjs (vortek skipped unless staged,
   vortek-* components filtered out of manifest)
   app/src/main/assets/runtime/manifest.json (vortek entries removed;
   matches the already-cleaned runtime.zip on device)

4) GitHub Actions build pipeline:
   .github/workflows/build-runtime.yml      (NEW)
   runtime/tests/verify-packaged-runtime.py (NEW, tested OK)
   .gitignore                               (+ excludes 288MB zip)
   runtime/scripts/build-shadps4-x86_64.sh  (+ fclose-guard patch line)
   runtime/scripts/build-shadps4-arm64.sh   (+ fclose-guard patch line)

NOT INCLUDED
------------
app/src/main/assets/runtime/runtime.zip (275MB, already cleaned in place;
GitHub rejects >100MB — CI regenerates it via build-runtime workflow).

VERIFY ANYTIME
--------------
python3 runtime/tests/verify-packaged-runtime.py \
  app/src/main/assets/runtime --no-vortek

STATUS
------
[x] manifest.json + runtime.zip verified consistent (443 files, hashes OK)
[ ] needs CI rebuild of box64 + shadps4 to actually ship the fixes
