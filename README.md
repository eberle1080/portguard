# portguard

Portguard is my own little project intended to allow LDAP users to punch holes in the firewall
for themselves. After a certain period of time (in incrememts defined by the sysadmin), the holes
are closed automatically. This is accomplished with a client-server system. A python daemon runs
on the router, opening / forwarding ports, and then closing them at a specified time. A PHP web
client allows users to communicate with this daemon.

This project runs under linux, and requires python, php (with xmlrpc), iptables, and apache. It is
released under the GPL v2 license.

## Goals

The usage scenario for this is simple. I'm at home, I want to access a service at work (which
sadly lives behind a NAT). I log in to the website with my LDAP credentials, open a few
ports for myself, and now I'm cooking with fire (or whatever the kids are cooking with these
days).

You're probably asking yourself, "and just what is wrong with ssh tunnels?" Good question, friend.
One word: iPhone. Also sometimes ssh tunnels just aren't practical.

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

This will allow any LDAP user to set up holes in the firewall for themselves. The only exception is that
the "remote IP" field is hard coded to the IP that they're logging in from. This prevents them from
opening ports for their friends. There are no other policy-related exceptions, that's up to you to code.
There's no way I can anticipate your particular needs.

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

The portguard program is a stateful program. What does this mean? Well if you go around restarting the daemon
all of your users' firewall exceptions WILL be reset. Why? It was easy, and c'mon are you really rebooting
your router that often? And if so, you've got problems that my program won't solve.

## Future ideas

These are JUST ideas. Odds are they'll never make it in to this program, but they sure are fun to think about.

*  Per-user persistent rules (just log in and all of your forwards are set up)
*  Keep-alive client (would make the timeout stuff obsolete, requires previous feature)
*  Logging (this one may make it in)
*  More advanced firewall exceptions (port ranges, SNAT / DNAT, simple forwarding without NAT)
*  Banning (block any IPs that fail to log in after n attempts)
