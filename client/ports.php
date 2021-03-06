<?php

if(!defined('INCLUDES'))
{
    die("Can't call this script directly!");
}

$host = $_SERVER['REMOTE_ADDR'];
$user = $_SESSION['user'];

if(!ping())
{
    print_header($user, $host);
    echo '<div style="margin-top: 10px;">Unable to contact portguard server :(</div>' . "\n";
    print_footer();
    exit;
}

if(isset($_POST['iport']) && array_key_exists($_POST['itimeout'], $config['TIMEOUTS']))
{
    $timeout = $config['TIMEOUTS'][$_POST['itimeout']];
    $port = (int)$_POST['iport'];
    $request = xmlrpc_encode_request('open', array($user, $host, $port, $timeout));
    runOpenRequest($request);
}
elseif(isset($_POST['fport']) && isset($_POST['fdsthost']) && isset($_POST['fdstport']) &&
       array_key_exists($_POST['ftimeout'], $config['TIMEOUTS']))
{
    $timeout = $config['TIMEOUTS'][$_POST['ftimeout']];
    $fport = (int)$_POST['fport'];
    $dsthost = trim($_POST['fdsthost']);
    $dstport = (int)$_POST['fdstport'];

    $request = xmlrpc_encode_request('forward', array($user, $host, $fport, $dsthost, $dstport, $timeout));
    runOpenRequest($request);
}

showPortPage($user, $host);

function print_header($user, $host)
{
    ?>
<html>
<head>
  <title>Open ports</title>
  <link href="style.css" rel="stylesheet" type="text/css">
</head>
<body>
  <div class="topbar">
    <div class="topleft">
      <?php echo getServerTime(); ?>
    </div>
    <div class="topright">
      <?php echo "$user@$host"; ?> [<a href="?logout">Log out</a>]
    </div>
  </div>
<?php
}

function print_footer()
{
?>
</body>
</html>
<?php
}

function routerTable($user, $host)
{
    global $config;
?>

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

<?php
    listOpenPorts();
?>

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
<?php
}

function forwardTable($user, $host)
{
    global $config;
?>

  <h2>Forward Ports</h2>
  <form method="post">
    <table class="mainTable">
      <thead>
        <tr>
          <th>User</th>
          <th>Remote IP</th>
          <th>Router Port</th>
          <th>Dest. Host</th>
          <th>Dest. Port</th>
          <th>Timeout</th>
        </tr>
      </thead>
      <tbody>
<?php
    listForwardPorts();
?>
        <tr>
          <td><input type="text" readonly="readonly" value="<?php echo $user; ?>" /></td>
          <td><input type="text" readonly="readonly" value="<?php echo $host; ?>" /></td>
          <td><input type="text" name="fport" /></td>
          <td><input type="text" name="fdsthost" /></td>
          <td><input type="text" name="fdstport" /></td>
          <td>
            <select name="ftimeout" style="width: 100%;">
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
          <td colspan="6" style="text-align: right;">
            <input type="submit" value="Open" />
          </td>
        </tr>

      </tbody>
    </table>
  </form>
<?php
}

function showPortPage($user, $host)
{
    print_header($user, $host);
    routerTable($user, $host);
    forwardTable($user, $host);
    print_footer();
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
        echo "Failed :(";
    }
}

function ping()
{
    global $config;

    $request = xmlrpc_encode_request('ping', array());
    $context = stream_context_create(array('http' => array(
        'method' => "POST",
        'header' => "Content-Type: text/xml\r\nUser-Agent: PHPRPC/1.0\r\nHost: " . $config["PG_HOST"] . "\r\n",
        'content' => $request
    )));

    $url = "http://" . $config["PG_HOST"] . ":" . $config["PG_PORT"] . "/pg";
    $file = @file_get_contents($url, false, $context);
    if($file == false)
        return false;

    $response = xmlrpc_decode($file);
    if(xmlrpc_is_fault($response))
        return false;
    if($response != 42)
        return false;

    return true;
}

function getServerTime()
{
    global $config;

    $request = xmlrpc_encode_request('now', array());
    $context = stream_context_create(array('http' => array(
        'method' => "POST",
        'header' => "Content-Type: text/xml\r\nUser-Agent: PHPRPC/1.0\r\nHost: " . $config["PG_HOST"] . "\r\n",
        'content' => $request
    )));

    $url = "http://" . $config["PG_HOST"] . ":" . $config["PG_PORT"] . "/pg";
    $file = @file_get_contents($url, false, $context);
    if($file == false)
        return "Cannot retrieve server time";

    $response = xmlrpc_decode($file);
    return date("m/d/Y g:i a", $response->timestamp);
}

function listOpenPorts()
{
    global $config;

    $request = xmlrpc_encode_request('list_open', array());
    $context = stream_context_create(array('http' => array(
        'method' => "POST",
        'header' => "Content-Type: text/xml\r\nUser-Agent: PHPRPC/1.0\r\nHost: " . $config["PG_HOST"] . "\r\n",
        'content' => $request
    )));

    $url = "http://" . $config["PG_HOST"] . ":" . $config["PG_PORT"] . "/pg";
    $file = file_get_contents($url, false, $context);

    $response = xmlrpc_decode($file);
    if (is_array($response) and xmlrpc_is_fault($response))
    {
        echo "Failed";
        return;
    }

    foreach($response as $item)
    {
        $user = $item[0];
        $remote = $item[1];
        $port = $item[2];
        $timeout = date("m/d/Y g:i a", $item[3]->timestamp);

echo <<<EOL
        <tr>
          <td>$user</td>
          <td>$remote</td>
          <td>$port</td>
          <td>$timeout</td>
        </tr>
EOL;
    }
}

function listForwardPorts()
{
    global $config;

    $request = xmlrpc_encode_request('list_forward', array());
    $context = stream_context_create(array('http' => array(
        'method' => "POST",
        'header' => "Content-Type: text/xml\r\nUser-Agent: PHPRPC/1.0\r\nHost: " . $config["PG_HOST"] . "\r\n",
        'content' => $request
    )));

    $url = "http://" . $config["PG_HOST"] . ":" . $config["PG_PORT"] . "/pg";
    $file = file_get_contents($url, false, $context);

    $response = xmlrpc_decode($file);
    if (is_array($response) and xmlrpc_is_fault($response))
    {
        echo "Failed";
        return;
    }

    foreach($response as $item)
    {
        $user = $item[0];
        $remote = $item[1];
        $port = $item[2];
        $dstHost = $item[3];
        $dstPort = $item[4];
        $timeout = date("m/d/Y g:i a", $item[5]->timestamp);

echo <<<EOL
        <tr>
          <td>$user</td>
          <td>$remote</td>
          <td>$port</td>
          <td>$dstHost</td>
          <td>$dstPort</td>
          <td>$timeout</td>
        </tr>
EOL;
    }
}
