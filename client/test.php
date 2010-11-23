<?php

$user = 'chris';
$host = '128.198.58.14';
$port = 42;
$timeout = 60;

$server_host = '127.0.0.1';
$server_port = 8000;

$request = xmlrpc_encode_request('open', array($user, $host, $port, $timeout));

$context = stream_context_create(array('http' => array(
    'method' => "POST",
    'header' => "Content-Type: text/xml\r\nUser-Agent: PHPRPC/1.0\r\nHost: $server_host\r\n",
    'content' => $request
)));

$url = "http://$server_host:$server_port/pg";
$file = file_get_contents($url, false, $context);

echo $file;
