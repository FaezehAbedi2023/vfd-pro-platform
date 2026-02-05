# ---------------- SETTINGS ----------------
$Container = "vfdpro_db"
$DbName    = "mydb"
$User      = "root"
$Pass      = "root123"


$LocalDumpDir = "G:\Southampton Uni\VFD Pro Platform\db_dumps"


$SharePointDir = "C:\Users\faezeh.net\VFD Pro Ltd\VFD Pro Working Content - db"

# ---------------- PREPARE ----------------
New-Item -ItemType Directory -Force -Path $LocalDumpDir | Out-Null
New-Item -ItemType Directory -Force -Path $SharePointDir | Out-Null


$stamp = Get-Date -Format "dd_MMM_yyyy"
$file  = "mydb_dump_$stamp.sql"
$localPath = Join-Path $LocalDumpDir $file
$spPath    = Join-Path $SharePointDir $file

# ---------------- DUMP ----------------
$cmd = "docker exec $Container mysqldump -u $User -p$Pass $DbName > `"$localPath`""
cmd /c $cmd


if (!(Test-Path $localPath) -or ((Get-Item $localPath).Length -lt 1000)) {
    throw "Dump failed or file too small: $localPath"
}

# ---------------- COPY TO SHAREPOINT ----------------
Copy-Item -Force $localPath $spPath


