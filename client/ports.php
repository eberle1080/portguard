<?php

if(!defined('INCLUDES'))
{
    die("Can't call this script directly!");
}

$host = $_SERVER['REMOTE_ADDR'];
$user = $_SESSION['user'];

if(!isset($_POST['iport']) && !isset($_POST['fport']) &&
   !isset($_POST['fdsthost']) && !isset($_POST['fdstport']))
{
    showPortPage($user, $host);
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

function showPortPage($user, $host)
{
    global $config;

    ?>
<html>
<head>
  <title>Open ports</title>
  <link href="style.css" rel="stylesheet" type="text/css">
</head>
<body>
  <div class="topbar">
    <div class="topleft">You are: <?php echo "$user@$host"; ?></div>
    <div class="topright"><a href="?logout">Log out</a></div>
  </div>

  <h2>Router Ports</h2>
  <form method="post">
    <table class="mainTable">
      <thead>
        <tr>
          <th>User</th>
          <th>Remote IP</th>
          <th>Router Port</th>
          <th>Timeout</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Bob</td>
          <td>1.2.3.4</td>
          <td>443</td>
          <td>12/22/2010 8:45 PM</td>
        </tr>

        <tr>
          <td><input type="text" readonly="readonly" value="<?php echo $user; ?>" /></td>
          <td><input type="text" readonly="readonly" value="<?php echo $host; ?>" /></td>
          <td><input type="text" name="iport" /></td>
          <td>
            <select name="itimeout" style="width: 100%;">
<?php
    foreach($config["TIMEOUTS"] as $key => $value)
    {
        if($key == $config['DEFAULT_TIMEOUT'])
            echo "              <option selected>$key</option>\n";
        else
            echo "              <option>$key</option>\n";
    }
?>
            </select>
          </td>
        </tr>

        <tr>
          <td colspan="4" style="text-align: right;">
            <input type="submit" value="Open" />
          </td>
        </tr>

      </tbody>
    </table>
  </form>
</body>
</html>
<?php

/*
    echo <<<EOL

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
*/

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
