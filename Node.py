import threading
import socket
import time
import os


# number of how many bytes can be sent/received at a time
BUFFER_SIZE = 4096
PORT = 1111

class Node:
    def __init__ ( self, port ):
        self.IP = self.setSelfIP ( )
        self.port = port
        self.clientSocketList = [ ]
        self.fileUpdateList = self.setFileUpdateList ( )

        threading.Thread ( target = self.listen ).start ( )
        self.findOpenPorts ( )
        threading.Thread ( target = self.checkForSelfUpdates ).start ( )
        threading.Thread ( target = self.receive ). start ( )
    
    
    # set the ip of this node 
    def setSelfIP ( self ):
        # get your ip address
        hostName = socket.gethostname ( )
        selfIP = socket.gethostbyname ( hostName )
        
        return selfIP
    
    
    def setFileUpdateList ( self ):
        fileUpdateList = [ ]

        # get all the file names inside the directory
        cwd = os.getcwd ( )
        fileNameList = os.listdir ( cwd )

        # go through all the files inside the directory
        for fileName in fileNameList:
            fileUpdate = [ ]
            fileLastModifiedTime = os.path.getmtime ( fileName )
            fileUpdate.append ( fileName )
            fileUpdate.append ( fileLastModifiedTime )

            fileUpdateList.append ( fileUpdate )

        return fileUpdateList
            
        
    # this thread will listen for people trying to connect to us. connect if they ask
    def listen ( self ):
        # make a socket
        selfServerSocket = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
        # bind it to the according IP and port
        selfServerSocket.bind ( ( self.IP, self.port ) )
        
        # now keep listening until the end of time :) and accept anyone who wants to connec to you
        while True:
            # listen for connection requests
            selfServerSocket.listen ( ) 
            
            ## accept anyone who's requested
            # connection is a new socket "usable to send and receive data on the connection"
            # remember that address is ( IP address, Port )
            clientSocket, clientIP = selfServerSocket.accept ( )
            print ( "Peer joined network with IP address " + str ( clientIP ) + ".\n" )
            self.clientSocketList.append ( clientSocket )
            #threading.Thread ( target = , args = clientSocket ).start ( )
        
        return 0

    

    # checks for any devices on your network with your target port open. connect if so
    # will probably remove this later so you can choose to connect to whatever connection you want with a given port
    def findOpenPorts ( self ):
        # split the ip address into their octets, and get the length of the last one
        lastOctetLength = len ( self.IP.split ( "." ) [ 3 ] )
        
        # record the ip address' first 3 octets by removing the last one
        firstThreeOctets = self.IP [ : -lastOctetLength ]
        
        
        ### check all connections on your network that start with the same three octets as your ip
        # get the arp table, which shows all connetions on your netowrk
        arpTable = os.popen ( 'arp -a' )
        
        # skip the first three lines of the string because they're just labels
        arpTable = arpTable.read ( )
        arpTable = arpTable.split ( self.IP )
        arpTable = arpTable [ 1 ].split ( "\n" ) [ 2 : ]

        # create a socket (?)
        s = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
        
        # go through every line in the arp table and get only the ip addresses with the same first three octets
        for line in arpTable:
            
            # only get the first "word" in the line of the arpTable, which is the ip address
            targetIP = line.split ( ) [ 0 ]
            
            # check if the IP have the same first three octets
            if firstThreeOctets in targetIP:
                # make sure this connection isnt already established
                doesExist = False
                for clientSocket in self.clientSocketList:
                    clientSocketIP = clientSocket.getpeername ( ) [ 0 ]
                    if clientSocketIP == targetIP:
                        doesExist = True

                # go ahead if not connected yet
                if not doesExist:
                    # try to connect to the target device on the given port
                    exception = s.connect_ex ( ( targetIP, self.port ) )
                    
                    #print ( "Checking if " + str ( targetIP ) + " is open on the port " + str ( self.port ) + "." )
                    # result will be 0 if successfully connected. else not
                    if exception == 0:
                        # if you get here, should push all your stuff to the guy you connected to.
                        print ( str ( targetIP ) + " is open. Connected.\n" )

                        self.clientSocketList.append ( s )
                    else:
                        print ( str ( targetIP ) + " is not open.\n" )

            if targetIP == "255.255.255.255":
                break
                    
        return 0


    
    # this thread will watch for any updates on itself
    def checkForSelfUpdates ( self ):
        # keep checking until the end of time
        while True:
            print ( "Checking self to see if any files were updated..." )
            
            # will be a list of lists
            # each list will have the updatedfile name and size
            updatedFiles = [ ]
            
            # get all the file names inside the directory
            cwd = os.getcwd ( )
            fileNameList = os.listdir ( cwd )
            #print ( fileNameList )
            
            # go through all the files inside the directory
            for fileName in fileNameList:
                isNewFile = True
                
                # get the size and lasttimemodified of the file 
                fileSize = os.path.getsize ( fileName )
                fileLastModifiedTime = os.path.getmtime ( fileName )
                
                #print ( "0." + fileName )
                #print ( "1." + str(fileSize) + " bytes" )
                #print ( "2." + str(fileLastModifiedTime ) + " time" )
                
                # compare this file to see if it's updated/new
                for fileUpdateIndex in range ( len ( self.fileUpdateList ) ):
                    # get recorded file info
                    fileUpdate = self.fileUpdateList [ fileUpdateIndex ]
                    
                    # check if the file matches any of the previous ones we've had
                    # if so, update the file if applicable
                    if fileName == fileUpdate [ 0 ]:
                        isNewFile = False
                        
                        # check if the lastmodified time has increased
                        if fileLastModifiedTime > fileUpdate [ 1 ]:
                            
                            # keep track of the updatedfile so we can send it later
                            print ( "Updated file found: " + fileName )
                            updatedFile = [ fileName, fileSize ]
                            updatedFiles.append ( updatedFile )

                            # update our records
                            newFileUpdate = [ fileName, fileLastModifiedTime ]
                            self.fileUpdateList [ fileUpdateIndex ] = newFileUpdate

                # if this file is a new file, update it to your peers
                if isNewFile == True:
                    # keep track of the updatedfile so we can send it later
                    print ( "New file found: " + fileName )
                    updatedFile = [ fileName, fileSize ]
                    updatedFiles.append ( updatedFile )

                    # update our old list
                    newFileUpdate = [ fileName, fileLastModifiedTime ]
                    self.fileUpdateList.append ( newFileUpdate )
                            
                    
            if len ( updatedFiles ) > 0:
                print ( "Sending updates to peers.\n" )
                self.send ( updatedFiles )
            
            else:
                print ( "No self updates found.\n" )

            
            time.sleep ( 10 )
            
        return 0
    
    
    
    # sends current node's new files to peers
    def send ( self, updatedFiles ):
        # go through all the clients in our list
        for clientSocket in self.clientSocketList:
            # go through all the files inside the directory
            # updatedFiles is a list of lists, where each list contains the name and size
            for file in updatedFiles:
                # get the size of the file 
                fileName = file [ 0 ]
                fileSize = file [ 1 ]
                #print ( "3." + str(fileName))
                #print ( "4." + str(fileSize))

                # send over metadata to the server. used to make sure all info is passed through
                metadata = ( fileName + " " + str ( fileSize ) ).encode ( )
                clientSocket.send ( metadata )


                # sleep for a bit, sometimes it sends too fast otherwise
                time.sleep ( 1 )


                ## next send over the data of the file
                # open the file
                with open ( fileName, "rb" ) as file:
                    fileSizeLeftToSend = fileSize

                    # send all parts of the file
                    while True:
                        # get the first chunk of the file
                        bytesRead = file.read ( BUFFER_SIZE )

                        # check if this is the last chunk of the buffer
                        if fileSizeLeftToSend <= 0:
                            break

                        # sleep for a bit, sometimes it sends too fast otherwise
                        time.sleep ( 0.1 )

                        # send over the data
                        clientSocket.sendall ( bytesRead )

                        # update our counter
                        fileSizeLeftToSend -= BUFFER_SIZE

                        file.flush ( )
                    
                    file.flush ( )
                    file.close ( )
                
        return 0
    
    
    
    def receive ( self ):
        # loop
        while True:
            # loop through all the clients to see if they've sent anything
            for clientSocket in self.clientSocketList:
                metadata = clientSocket.recv ( BUFFER_SIZE ).decode ( )

                # gets here if something was sent. split the metadata 
                metadata = metadata.split ( )
                fileDirectory = metadata [ 0 ]
                fileSize = metadata [ 1 ]
                    
                # clean up the metadata. remove directory from filename and turn filesize into an int
                fileName = os.path.basename ( fileDirectory )
                fileSizeLeftToReceive = int ( fileSize )

                clientSocketIP = clientSocket.getpeername ( ) [ 0 ]
                print ( "Peer with IP address " + clientSocketIP + " sent a file: " + fileName )
                
                # open the file
                with open ( fileName, "wb" ) as file:
                    fileBytes = b''
                    
                    # read and write all parts of the file
                    while True:
                        # read the bytes we just received
                        bytesReceived = clientSocket.recv ( BUFFER_SIZE )
                        
                        # check if this is the last chunk of the buffer
                        if fileSizeLeftToReceive <= 0:
                            break
                        
                        # write the bytes to the file
                        fileBytes += bytesReceived
                        
                        # update our counter
                        fileSizeLeftToReceive -= BUFFER_SIZE

                        file.flush ( )

                    # write the contents to the file and close it
                    file.write ( fileBytes )
                    file.flush ( )
                    file.close ( )
            
        return 0
    
    


node = Node ( PORT )
