from pymysql import connections, cursors, connect

def connection():
    conn = connect(host="localhost", 
                   user='root',
                   password='zaq1@WSX',
                   db='pythonprogramming')
    
    c = conn.cursor()

    return c, conn
    