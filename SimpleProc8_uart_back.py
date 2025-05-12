import serial
import threading
import time

class UARTInterface:
    def __init__(self, cpu, uart_device='/dev/ttys002', baud_rate=9600):
        self.cpu = cpu
        self.uart_device = uart_device
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.running = False
        self.rx_thread = None
        
        # Override the CPU's UART TX function
        cpu.uart_tx_byte = self.uart_tx_byte
    
    def connect(self):
        """Connect to the UART device."""
        try:
            self.serial_conn = serial.Serial(
                port=self.uart_device,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            
            self.cpu.uart_connected = True
            self.running = True
            
            # Start RX thread
            self.rx_thread = threading.Thread(target=self.uart_rx_thread)
            self.rx_thread.daemon = True
            self.rx_thread.start()
            
            print(f"Connected to UART device: {self.uart_device}")
            return True
            
        except Exception as e:
            print(f"Error connecting to UART: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from the UART device."""
        self.running = False
        
        if self.rx_thread:
            self.rx_thread.join(timeout=1.0)
        
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
        
        self.cpu.uart_connected = False
        print("Disconnected from UART device")
    
    def uart_rx_thread(self):
        """Thread to handle UART receive operations."""
        print(f"UART RX thread started on port {self.uart_device}")
        
        # Clear any stale data
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.reset_input_buffer()
        
        check_count = 0
        
        while self.running:
            try:
                # Check if connection is valid
                if not self.serial_conn or not self.serial_conn.is_open:
                    print("UART connection lost")
                    continue
                
                # Print status occasionally
                check_count += 1
                if check_count % 500 == 0:  # Every ~5 seconds (500 * 0.01s)
                    #print(f"UART RX checking: in_waiting={self.serial_conn.in_waiting}")
                    # Try writing a test byte to keep connection active
                    try:
                        self.serial_conn.write(b'\x00')  # Send null byte as keepalive
                        self.serial_conn.flush()
                    except:
                        pass
                
                # Check for data with timeout
                bytes_waiting = self.serial_conn.in_waiting
                if bytes_waiting > 0:
                    #print(f"Data detected! {bytes_waiting} bytes waiting")
                    data = self.serial_conn.read()
                    if data:
                        byte_value = data[0]
                        char_repr = chr(byte_value) if 32 <= byte_value <= 126 else ''
                        #print(f"UART RX received: 0x{byte_value:02X} ('{char_repr}')")
                        
                        # Call the CPU's uart_rx_byte method
                        result = self.cpu.uart_rx_byte(byte_value)
                        #print(f"CPU processed byte: {result}")
                        
                        # Verify CPU memory updates
                        head = self.cpu.memory[0xF6]
                        tail = self.cpu.memory[0xF7]
                        #print(f"UART buffer: head={head}, tail={tail}")
                        #print(f"UART status: 0x{self.cpu.memory[0xF0]:02X}")
            
            except Exception as e:
                print(f"Error in UART RX thread: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(0.5)  # Longer delay on error
        
        print("UART RX thread terminated")
    
    def uart_tx_byte(self, byte):
        """Transmit a byte over UART."""
        if self.serial_conn:
            try:
                self.serial_conn.write(bytes([byte & 0xFF]))
                self.serial_conn.flush()
                return True
            except Exception as e:
                print(f"Error sending UART data: {str(e)}")
        
        return False
