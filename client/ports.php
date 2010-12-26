<?php

if(!defined('INCLUDES'))
{
    die("Can't call this script directly!");
}

$host = $_SERVER['REMOTE_ADDR'];
$user = $_SESSION['user'];

$timeout = 60;

if(!isset($_POST['iport']) && !isset($_POST['fport']) &&
   !isset($_POST['fdsthost']) && !isset($_POST['fdstport']))
{
    echo <<<EOL
<html><head><title>Open ports</title></head><body>
<h1>You are: $user@$host</h1>
<h2>Open port directly to router ($timeout minute timeout)</h2>
<form method="post"><table><tr>
<td>Router port:</td>
<td><input type="text" name="iport" /></td>
</tr>
<tr>
<td colspan="2"><input type="submit" value="Open" /></td>
</tr>
</table></form>

<h2>Forward a port through the router ($timeout minute timeout)</h2>
<form method="post"><table><tr>
<td>Router port:</td>
<td><input type="text" name="fport" /></td>
</tr><tr>
<td>Desination IP:</td>
<td><input type="text" name="fdsthost" /></td>
</tr><tr>
<td>Desination port:</td>
<td><input type="text" name="fdsthost" /></td>
</tr><tr>
<td colspan="2" stlye="text-align: right;">
<input type="submit" value="Forward" />
</td></tr>
</table></form>
</body></html>
EOL;
}
elseif(isset($_POST['iport']))
{
    $port = (int)$_POST['iport'];
    $request = xmlrpc_encode_request('open', array($user, $host, $port, $timeout * 60));
    runOpenRequest($request);
}
elseif(isset($_POST['fport']) || isset($_POST['fdsthost']) || isset($_POST['fdstport']))
{
    $fport = (int)$_POST['fport'];
    $dsthost = trim($_POST['fdsthost']);
    $dstport = (int)$_POST['fdstport'];
    $request = xmlrpc_encode_request('forward', array($user, $host, $fport, $dsthost, $dstport, $timeout * 60));
    runOpenRequest($request);
}
else
{
    die("Unknown error");
}

function runOpenRequest($request)
{
    global $config;

    $context = stream_context_create(array('http' => array(
        'method' => "POST",
        'header' => "Content-Type: text/xml\r\nUser-Agent: PHPRPC/1.0\r\nHost: " . $config["PG_HOST"] . "\r\n",
        'content' => $request
    )));

    $url = "http://" . $config["PG_HOST"] . ":" . $config["PG_PORT"] . "/pg";
    $file = file_get_contents($url, false, $context);

    $response = xmlrpc_decode($file);
    if (is_array($response) and xmlrpc_is_fault($response)){
        echo "Failed";
    } else {
        echo "It worked! Maybe... give it a shot :\\";
    }
}
