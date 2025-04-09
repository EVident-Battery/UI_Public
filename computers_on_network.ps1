$FileOut = ".\Computers.csv"
$Subnet = "10.1.10."

# Phase 1: Ping subnet
Write-Host "PROGRESS:PHASE1" # Signal start of ping phase
$Total = 254
$Current = 0

1..254 | ForEach-Object {
    $Current++
    Write-Host "PROGRESS:PING:$Current/$Total"
    Start-Process -WindowStyle Hidden ping.exe -Argumentlist "-n 1 -l 0 -f -i 2 -w 1 -4 $SubNet$_"
}

# Phase 2: ARP scanning
Write-Host "PROGRESS:PHASE2" # Signal start of ARP phase
$arpOutput = arp.exe -a | Select-String "$SubNet.*dynam"
$Total = @($arpOutput).Count
$Current = 0

$Computers = @()
$arpOutput | ForEach-Object {
    $Current++
    Write-Host "PROGRESS:ARP:$Current/$Total"
    
    $line = $_ -replace ' +',','
    $obj = $line | ConvertFrom-Csv -Header Computername,IPv4,MAC,x,Vendor | Select Computername,IPv4,MAC
    
    # Resolve hostname
    nslookup $obj.IPv4 | Select-String -Pattern "^Name:\s+([^\.]+).*$" | ForEach-Object {
        $obj.Computername = $_.Matches.Groups[1].Value
    }
    
    $Computers += $obj
}

Write-Host "PROGRESS:DONE"
$Computers
$Computers | Export-Csv $FileOut -NotypeInformation
#$Computers | Out-Gridview