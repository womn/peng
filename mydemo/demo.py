

if __name__ == '__main__':
    try:
        while True:
            mac = input()
            mac_str = ':'.join(mac[i:i+2] for i in range(0,12,2))
            if re.match(r"^\s*([0-9a-fA-F]{2,2}:){5,5}[0-9a-fA-F]{2,2}\s*$", mac_str):
                print(mac_str)
                break
    except KeyboardInterrupt:
        sys.exit(0)