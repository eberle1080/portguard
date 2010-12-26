<?php

define('LDAP_SERVER', 'ldap.chriseberle.net');
define('LDAP_PORT', 389);
define('LDAP_TOP', 'ou=People,dc=chriseberle,dc=net');
define('INCLUDES', 1);

//if($_SERVER["HTTPS"] != "on")
//{
//    header("HTTP/1.1 301 Moved Permanently");
//    header("Location: https://" . $_SERVER["SERVER_NAME"] . $_SERVER["REQUEST_URI"]);
//    exit();
//}

$inactive = 10 * 60; // 10 minutes

session_start();

function LDAPconnect()
{
    $ds = ldap_connect(LDAP_SERVER, LDAP_PORT);
    if (!$ds) {
        return FALSE;
    }

    if (!ldap_set_option($ds, LDAP_OPT_PROTOCOL_VERSION, 3)) {
        @ldap_close($ds);
        return FALSE;
    }
    return $ds;
}

function LDAPauth($rdn, $passwd)
{
    $ds = LDAPconnect();
    $dn = $rdn .",". LDAP_TOP;

    if (!@ldap_bind($ds, $dn, $passwd)) {
        return FALSE;
    }
    return $ds;
}

function showLogin()
{
?>
<html>
<head>
  <title>Login please</title>
  <link href="style.css" rel="stylesheet" type="text/css">
</head>
<body>
  <form method="post">
  <table id="login">

    <tr>
      <td>Name:</td>
      <td><input type="text" name="luname" /></td>
    </tr>

    <tr>
      <td>Pass:</td>
      <td><input type="password" name="lupass" /></td>
    </tr>

    <tr>
      <td colspan="2" style="text-align: right;">
        <input type="submit" value="Log in" />
      </td>
    </tr>

  </table>
  </form>
</body>
</html>
<?php
}

function processLogin()
{
    $uname = "uid=" . trim($_POST['luname']);
    $upass = trim($_POST['lupass']);

    LDAPconnect();
    if(!LDAPauth($uname, $upass))
    {
        echo "Fail";
    }
    else
    {
        $_SESSION['logged_in'] = true;
        $_SESSION['user'] = trim($_POST['luname']);

        header("Location: " . $_SERVER['PHP_SELF']);
    }
}

function showMainPage()
{
    if(isset($_SESSION['timeout']))
    {
        $session_life = time() - $_SESSION['timeout'];
        if($session_life > $inactive)
        {
            session_destroy();
            header("Location: " . $_SERVER['PHP_SELF']);
            exit();
        }
    }

    if(isset($_GET['logout']))
    {
        session_destroy();
        header("Location: " . $_SERVER['PHP_SELF']);
        exit();
    }

    $_SESSION['timeout'] = time();

    require 'ports.php';
}

if(!isset($_SESSION['logged_in']) || $_SESSION['logged_in'] != true)
{
    if(!isset($_POST['luname']) && !isset($_POST['lupass']))
    {
        showLogin();
    }
    else
    {
        processLogin();
    }
}
else
{
    showMainPage();
}
