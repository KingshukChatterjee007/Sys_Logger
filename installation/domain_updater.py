
#!/usr/bin/env python3
import time, json, requests, os
CONFIG="E:\PROJECTS\Sys_Logger\installation\unit_client_config.json"

while True:
    if os.path.exists(CONFIG):
        cfg=json.load(open(CONFIG))
        url=cfg.get("server_url")
        if url:
            try:
                r=requests.get(f"{url}/api/domain_config",timeout=10)
                if r.status_code==200:
                    cfg.update(r.json())
                    json.dump(cfg,open(CONFIG,"w"),indent=4)
            except:
                pass
    time.sleep(3600)
