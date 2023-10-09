declare void @exit(i32)

declare i32 @socket(i32, i32, i32)
declare i32 @connect(i32, i8*, i32)
declare i32 @send(i32, i8*, i32, i32)
declare i32 @recv(i32, i8*, i32, i32)
declare i32 @close(i32)

define i32 @main() {
    ; Create a socket
    %socket = call i32 @socket(i32 2, i32 1, i32 0)
    
    ; Specify the server's address
    %server_addr = alloca [16 x i8]
    store [16 x i8] c"142.250.64.46\00", [16 x i8]* %server_addr
    
    ; Connect to the server
    %connect_result = call i32 @connect(i32 %socket, i8* %server_addr, i32 16)
    
    ; Send the GET request
    %request = alloca [256 x i8]
    store [256 x i8] c"GET / HTTP/1.1\r\nHost: www.google.com\r\nConnection: close\r\n\r\n\00", [256 x i8]* %request
    %send_result = call i32 @send(i32 %socket, i8* %request, i32 68, i32 0)
    
    ; Receive and print the response
    %response = alloca [1024 x i8]
    %recv_result = call i32 @recv(i32 %socket, i8* %response, i32 1024, i32 0)
    %response_len = load i32, i32* %recv_result
    %response_str = getelementptr [1024 x i8], [1024 x i8]* %response, i32 0, i32 0
    call i32 (i8*, ...)* @printf(i8* c"%.*s\00", i32 %response_len, i8* %response_str)
    
    ; Close the socket
    call i32 @close(i32 %socket)
    
    ret i32 0
}
