function New-IntervalPing {
    [Alias("iping")]
    Param(
        [string]$ComputerName,
        [int]$Count = 4,
        [int]$TimeOut = 100,
        [int]$Interval = 500
    )
    1..$Count | ForEach-Object {
        $Ping = [System.Net.NetworkInformation.Ping]::New()
        $Ping.Send($ComputerName, $TimeOut)
        start-sleep -Milliseconds $Interval
    }
}