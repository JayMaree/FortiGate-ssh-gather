import sys
import threading
import paramiko

__connections__ = {}
__hosts__ = {}

FORTIGATES = [
    {
        "host":"fg0.domain.com",
        "username":"admin",
        "password":"password123"
    },
    {
        "host":"fg1.domain.com",
        "username":"admin",
        "password":"password123"
    }
]


def connect(host, kwargs={}):
    hostname = False
    __hosts__[host] = kwargs
    if "host" in kwargs:
        hostname = kwargs["host"]
        kwargs.pop("host")
    if host in __connections__:
        return __connections__[host]
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, **kwargs)
        __connections__[host] = ssh
    except Exception as error:
        pass
    if hostname:
        kwargs["host"] = hostname
    return ssh

def close(host):
    if host in __connections__:
        try:
            __connections__[host].close()
            del __connections__[host]
        except Exception as error:
            pass

def connect_all(host_array):
    for host in host_array:
        try:
            hostname = host["host"]
            connect(hostname, host)
        except Exception as error:
            print hostname, error

def close_all():
    for host in __connections__:
        try:
            __connections__[host].close()
        except Exception as error:
            print error
    __connections__.clear()

def run_all(command, threads=True, **kwargs):
    thread_list = []
    for host in __connections__:
        try:
            if threads:
                task = threading.Thread(target=run, \
                    args=(host, command), kwargs=kwargs)
                thread_list.append(task)
                task.start()
            else:
                run(host, command, **kwargs)
        except Exception as error:
            print error
    for task in thread_list:
        task.join()

def run(host, command, **kwargs):
    if host in __connections__:
        try:
            hostconn = __connections__[host]
            if isinstance(command, list):
                for i in xrange(0, len(command)):
                    run_command(hostconn, host, command[i], **kwargs)
            else:
                run_command(hostconn, host, command, **kwargs)
        except Exception as error:
            print host, error

def run_command(hostconn, host, command, print_host=False, \
    output=sys.stdout.write, sudo=False, **kwargs):
    if sudo and host in __hosts__ and "password" in __hosts__[host]:
        command = "echo \"{}\" | sudo -SE {}".format(__hosts__[host]["password"], command)
    stdin, stdout, stderr = hostconn.exec_command(command)
    lines_iterator = iter(stdout.readline, b"")
    for line in lines_iterator:
        if print_host:
            line = host + " " + line
        output(line)
    lines_iterator = iter(stderr.readline, b"")
    for line in lines_iterator:
        if print_host:
            line = host + " " + line
        output(line)

def put_all(local_path, remote_path, threads=True, **kwargs):
    thread_list = []
    for host in __connections__:
        try:
            if threads:
                task = threading.Thread(target=put, \
                    args=(host, local_path, remote_path))
                thread_list.append(task)
                task.start()
            else:
                put(host, local_path, remote_path)
        except Exception as error:
            print error
    for task in thread_list:
        task.join()

def put(host, local_path, remote_path):
    if host in __connections__:
        try:
            hostconn = __connections__[host]
            sftp = paramiko.SFTPClient.from_transport(hostconn.get_transport())
            sftp.put(local_path, remote_path)
        except Exception as error:
            print host, error

def main():
    print 'Connecting with the defined FortiGate devices'
    connect_all(FORTIGATES)
    print 'Sending the command...'
    run_all("get sys status")
    print 'Executed.'
    close_all()

if __name__ == '__main__':
main()
