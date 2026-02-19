param(
    [Parameter(Mandatory=$false, HelpMessage="Samples count")]
    [Alias("c")]
    [int]$SamplesCount = 10,
    [Parameter(Mandatory=$false, HelpMessage="Resulted folder")]
    [Alias("f")]
    [string]$folder,
    [Parameter(Mandatory=$false, HelpMessage="Sleep between photo, ms")]
    [Alias("d")]
    [int]$sleep_ms = 10
)

# $sleep_ms = 30 * 1000

for ($i = 1; $i -le $SamplesCount; $i++) {
    poetry run python ./takeSinglePhoto.py -f $folder
    Start-Sleep -Milliseconds $sleep_ms
}