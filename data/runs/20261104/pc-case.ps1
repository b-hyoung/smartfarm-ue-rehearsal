[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('1', '2', '3', '4')]
    [string]$Number,

    [Parameter(Mandatory)]
    [ValidateSet('Prepare', 'Run')]
    [string]$Action
)

$cases = @{
    '1' = '01_ac_only'
    '2' = '02_ac_all'
    '3' = '03_ac_lower'
    '4' = '04_ac_upper'
}
$caseName = $cases[$Number]
$containerName = "sf-20261104-$caseName"
$mounts = @(
    '--mount', "type=bind,source=$PSScriptRoot,target=/study,readonly"
    '--mount', "type=volume,source=$containerName,target=/work"
)
[string[]]$options = if ($Action -eq 'Prepare') { '--rm' } else { '-d', '--name', $containerName }
& docker run @options @mounts opencfd/openfoam-default:2512 bash /study/case.sh $Action.ToLowerInvariant() $caseName
exit $LASTEXITCODE
