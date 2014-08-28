-Recon Command example
	python main.py Recon -f  recon/dictionaries/hostnames.txt -d <target_domain> -n -s 
		(dictionary based dns lookups with salt)
		
	python main.py Recon -f recon/dictionaries/hidden_paths.txt -d <target_domain> -w -u
		(scan your webserver for hidden paths)
		
	python main.py Recon -i 192.168.1.1-192.168.254.254 -W -n
		(reverse dns and whois lookup of ip range)
		
	python main.py Recon -d <target_domain> -e
		(google email search for domain)
		
	python main.py Recon -f recon/dictionaries/google_queries.txt -g -Q -d <target_domain>
		(query google with some google hacking queries for your domain)
		
	python main.py Recon -h
		(Show usage for command options)
		
-Dork Command example
	python main.py Dork -f dork/dorks.txt -d <target_domain> -s
		(sql injection scanning)
	
	python main.py Dork -f dork/dorks.txt -d <target_domain> -l
		(LFI scanning)
	
	python main.py Dork -f dork/dorks.txt -d <target_domain> -r
		(RFI scanning)
	
	python main.py Dork -f dork/dorks.txt -d <target_domain> -x
		(XSS scanning)
	
	python main.py Dork -h
		(Show usage for command options)
		
-Dns command example
	python main.py Dns -w dns_geoip/word.txt -x dns_geoip/GeoLiteCity.dat -d <target_domain>
		(dns bruteforce with geoip lookups)
		
	python main.py Dns -h
		(Show usage for command options)
		
-Admin command example
	python main.py Admin -f dir_admin/directory -s <target_site_url>
		(find pages which is in directory file)
	
	python main.py Admin -h
		(Show usage for command options)
		
-LoadBal command example
	python main.py LoadBal -s <target_site_url> -d
		(Load Balance Detecting)
	
	python main.py LoadBal -h
		(Show usage for command options)	
		
-WAF command example
	python main.py WAF -s <target_site_url> -a
		(find all WAFs)
		
	python main.py WAF -h
		(Show usage for command options)	

-WAAF command example
	python main.py WAAF -u <target_site_url>
		(Scan a single URL for FI errors)
		
	python main.py WAAF -h
		(Show usage for command options)

-WIFI command example
	python main.py WIFI -wpa
                (Only target WPA networks (works with -wps -wep))

        python main.py WIFI -h
                (Show usage for command options)

-HASH command example
        python main.py HASH MD5 -h <hash>
                (Try to crack only one hash)

        python main.py HASH -h
                (Show usage for command options)

-dbAttack command example
	python main.py dbAttack 78.34.12.120
                (Check for default credentials on a MySQL server)

        python main.py dbAttack -h
                (Show usage for command options)

-svmap command example
	python main.py svmap 10.0.0.1-10.0.0.255 172.16.131.1 sipvicious.org/22 10.0.1.1/241.1.1.1-20 1.1.2-20.* 4.1.*.*
	python main.py svmap -s session1 --randomize 10.0.0.1/8
	python main.py svmap --resume session1 -v
	python main.py svmap -p5060-5062 10.0.0.3-20 -m INVITE
		(Scans for SIP devices on a given network)

	python main.py svmap -h
                (Show usage for command options)

-svwar command example
	python main.py svwar -e100-999 10.0.0.1
	python main.py svwar -d dictionary.txt 10.0.0.2
		(Identifies active extensions on a PBX)

	python main.py svwar -h
                (Show usage for command options)

-svcrack command example
	python main.py svcrack -u100 -d dictionary.txt 10.0.0.1
	python main.py svcrack -u100 -r1-9999 -z4 10.0.0.1
		(An online password cracker for SIP PBX)

	python main.py svcrack -h
                (Show usage for command options)

-svreport command example
	python main.py svreport list
	python main.py svreport export -f pdf -o scan1.pdf -s scan1
	python main.py svreport delete -s scan1
		(Get sessions and exports reports to various formats)

	python main.py svreport -h
                (Show usage for command options)

-svcrash command example
        python main.py svcrash --auto
                (Automatically send responses to attacks)

        python main.py svcrash -h
                (Show usage for command options)

