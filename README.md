# portguard

This little project is intended to be a client-server system. The server is written in python
and runs on a router (specifically a NAT router). It accepts connections from the client. It
opens ports for a set amount of time (specified in seconds), and then closes the hole. It is
designed so that you can open a port for yourself wherever you are. It uses XMLRPC for
communication. The client is written in PHP. Technically, no authentication is necessary,
but I figured it would be a good idea to force people to log in. Once logged in, users can
open ports for themselves using the web interface.

## Goals

The usage scenario for this is simple. I'm at home, I want to access a service at work (which
sadly lives behind a NAT). I log in to the website with my LDAP credentials, open a few
ports for myself, and now I'm cooking with fire (or whatever the kids are cooking with these
days).

## Setup

First of all, I ain't your sysadmin. It's up to you to determine how best to integrate this into
your setup. I assume that you're competent enough to set up an apache host (virtual or otherwise)
and that you already have an iptables firewall set up. Also you'll need a working ldap setup. If
you don't know how to do these things, go educate yourself. 

### iptables

Before you can use portguard, you need to set up your iptables for it. Now since I don't know your
firewall rules, it's up to you to find the best place to place these rules.

    $> iptables -N portguard
    $> iptables -t nat -N portguard
    $> iptables -A portguard -j RETURN
    $> iptables -I INPUT -j portguard
    $> iptables -t nat -A portguard -j RETURN
    $> iptables -t nat -I PREROUTING -j portguard
    $> iptables -A INPUT -i ${INTERNAL_INTERFACE} -s ${APACHE_HOST} -p tcp --dport 8812 -j ACCEPT
    $> iptables -A INPUT -p tcp -s \! ${APACHE_HOST} --dport 8812 -j DROP

### Portguard daemon

The portguard daemon runs on the NAT router. Download the portguard code, and copy the program files
in the "daemon" directory to a location of your choosing. Personally I suggest /usr/local/portguard.
If you're dead-set against using port 8812 you can edit portguard.py and change the port number.
To run the portguard daemon, run the following command (as root):

    $> portguardd.py start

If you want this starting up at boot, I trust you're smart enough to add this command to /etc/rc.local.
The portguardd program also accepts "stop" and "restart" as valid commands, which do exactly what you
think.

### Portguard PHP client

The portguard PHP client can be run anywhere (technically) but it should be run on a host behind
(or on) the NAT router. Download the portguard code and copy the files in the "client" directory into a
directory for apache. Set the owner / group permissions accordingly. Set up a virtual host (or whatever
you decide is appropriate) for this install.

Once you've gotten the PHP client installed and apache configured, it's time to configure the client.
Find the config.php.sample file, and copy it to a new file called config.php. Edit it to your liking.
There are comments describing each option. 

Restart apache, throw some chicken bones, do a rain dance, whatever your rituals are. Now try to navigate
to your php install. For example, fire up a web browser and go to http://portguard.domain.tld/

## Usage

Make sure that the portguard daemon is running before you do anything. Log in to the website, and you'll
see a pretty simple interface. There are two forms. One will allow you to open a port (from wherever you
are) directly to the router. The other will allow you to create a forward to a host behind the router.
You can technically use this site from BEHIND the NAT, but it won't do anything particularly exciting. 
The most important option is timeout which determines how long the exception will be available.

This will allow any LDAP user to set up holes in the firewall for themselves. There are no exceptions,
that's up to you to code. There's no way I can anticipate your policies.

## Security

Obviously this thing has a big potential for abuse. For one, unless you're feeling really REALLY lucky
make sure that the php client is running on an SSL-only connection. Secondly make sure that your iptables
rules are set up such that ONLY the php host can communicate with the portguard daemon. It's a very
simple XML-RPC interface with no authentication, so make sure that no one else (especially on the outside)
can connect to the portguard daemon.

## Notes

One thing to keep in mind: there's no reason to be concerned about a user screwing things up for everyone.
Rules are on a per-ip basis, which means that if Joe forwards port 123 somewhere, port 123 is still
available for the rest of the users (as long as they're behind a different remote IP). Again, any changes
in the program's behavior you wish to see can be accomplished by (say it with me) changing the code.
