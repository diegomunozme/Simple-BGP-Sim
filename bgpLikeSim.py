# Task: Create some functions for a simplified BGP router
#   Specifically, the withdraw, update, and next_hop functions of the Router
#   The class Route will be used.
# 
#   withdraw(rt) - rt is type Route.   
#


class Route:
    # A prefix is in form 
    neighbor = ""  # The router that send this router - will be a.b.c.d
    prefix = ""    # The IP address portion of a prefix - will be a.b.c.d
    prefix_len = 0 # The length portion of a prefix - will be an integer
    path = []      # the AS path - list of integers

    def __init__(self, neigh, p, plen, path):
        self.neighbor = neigh
        self.prefix = p
        self.prefix_len = plen
        self.path = path 

    # convert Route to a String    
    def __str__(self):
        return self.prefix+"/"+str(self.prefix_len)+"- ASPATH: " + str(self.path)+", neigh: "+self.neighbor

    # Get the prefix in the a.b.c.d/x format
    def pfx_str(self):
        return self.prefix+"/"+str(self.prefix_len)


# Implement the following functions:
#  update - the router received a route advertisement (which can be a new one, or an update
#         - the function needs to store the route in the RIB
#  withdraw - the router received a route withdraw message
#          - the function needs to delete the route in the RIB
#  nexthop - given ipaddr in a.b.c.d format as a string (e.g., "10.1.2.3"), perform a longest prefix match in the RIB
#          - Select the best route among multiple routes for that prefix by path length.  
#          - if same length, return either

class Router:
    rib = {}

    def printRIB(self):
        for pfx in self.rib.keys():
            for route in self.rib[pfx]:
                print(route)

    def update(self, rt):
        pfx = rt.pfx_str()
        if pfx not in self.rib:
            self.rib[pfx] = [rt]
        else:
            # Check if a route from the same neighbor exists
            updated = False
            for i, route in enumerate(self.rib[pfx]):
                if route.neighbor == rt.neighbor:
                    self.rib[pfx][i] = rt  # Replace the existing route
                    updated = True
                    break
            if not updated:
                self.rib[pfx].append(rt)  # Add a new route for the prefix
        return

    def withdraw(self, rt):
        pfx = rt.pfx_str()
        if pfx in self.rib:
            # Remove the route matching the neighbor
            self.rib[pfx] = [route for route in self.rib[pfx] if route.neighbor != rt.neighbor]
            # If no routes left for this prefix, remove the entry
            if not self.rib[pfx]:
                del self.rib[pfx]
        return

    def convertToBinaryString(self, ip):
        vals = ip.split(".")
        a = format(int(vals[0]), 'b').rjust(8, '0')
        b = format(int(vals[1]), 'b').rjust(8, '0')
        c = format(int(vals[2]), 'b').rjust(8, '0')
        d = format(int(vals[3]), 'b').rjust(8, '0')
        return a+b+c+d

    def next_hop(self, ipaddr):
        ip_bin = self.convertToBinaryString(ipaddr)
        longest_match_len = -1
        best_route = None

        for pfx in self.rib:
            pfx_ip, pfx_len = pfx.split('/')
            pfx_len = int(pfx_len)
            pfx_bin = self.convertToBinaryString(pfx_ip)

            # Check if this prefix matches the start of the IP address
            if ip_bin.startswith(pfx_bin[:pfx_len]):
                # We found a matching prefix, now check if it's the longest match
                if pfx_len > longest_match_len:
                    longest_match_len = pfx_len
                    # Find the route with the shortest AS path
                    best_route = min(self.rib[pfx], key=lambda rt: len(rt.path))
                elif pfx_len == longest_match_len:
                    # Handle tie by choosing any of the best routes
                    candidate_route = min(self.rib[pfx], key=lambda rt: len(rt.path))
                    if len(candidate_route.path) < len(best_route.path):
                        best_route = candidate_route

        return best_route.neighbor if best_route else None


def test_cases():
    rtr = Router()

    print("=== Test 1: Withdrawing a non-existent route ===")
    rtr.withdraw(Route("1.1.1.1", "10.0.0.0", 24, [3, 4, 5]))

    print("=== Test 2: Updating RIB with new routes ===")
    rtr.update(Route("1.1.1.1", "10.0.0.0", 24, [3, 4, 5]))
    rtr.update(Route("2.2.2.2", "10.0.0.0", 24, [1, 2]))
    rtr.printRIB()

    print("=== Test 3: Overwriting an existing route from a neighbor ===")
    rtr.update(Route("2.2.2.2", "10.0.0.0", 24, [1, 22, 33, 44]))
    rtr.printRIB()

    print("=== Test 4: Updating with overlapping prefix ===")
    rtr.update(Route("2.2.2.2", "10.0.0.0", 22, [4, 5, 7, 8]))
    rtr.printRIB()

    print("=== Test 5: Updating with a completely different prefix ===")
    rtr.update(Route("2.2.2.2", "12.0.0.0", 16, [4, 5]))
    rtr.update(Route("1.1.1.1", "12.0.0.0", 16, [1, 2, 30]))
    rtr.printRIB()

    print("=== Test 6: Finding next hop for an IP address with no match ===")
    nh = rtr.next_hop("10.2.0.13")
    print(f"Next hop for 10.2.0.13: {nh}")
    assert nh is None

    print("=== Test 7: Finding next hop for an IP address with a match ===")
    nh = rtr.next_hop("10.0.0.13")
    print(f"Next hop for 10.0.0.13: {nh}")
    assert nh == "1.1.1.1"

    print("=== Test 8: Withdrawing a route and checking next hop ===")
    rtr.withdraw(Route("1.1.1.1", "10.0.0.0", 24, [3, 4, 5]))
    nh = rtr.next_hop("10.0.0.13")
    print(f"Next hop for 10.0.0.13 after withdrawal: {nh}")
    assert nh == "2.2.2.2"

    print("=== Test 9: Re-announcing and checking next hop ===")
    rtr.withdraw(Route("1.1.1.1", "10.0.0.0", 24, [3, 4, 5]))
    rtr.update(Route("2.2.2.2", "10.0.0.0", 22, [4, 5, 7, 8]))
    nh = rtr.next_hop("10.0.1.77")
    print(f"Next hop for 10.0.1.77: {nh}")
    assert nh == "2.2.2.2"

    print("=== Test 10: Finding next hop for a different prefix ===")
    nh = rtr.next_hop("12.0.12.0")
    print(f"Next hop for 12.0.12.0: {nh}")
    assert nh == "2.2.2.2"

    print("=== Test 11: Updating and checking next hop ===")
    rtr.update(Route("1.1.1.1", "20.0.0.0", 16, [4, 5, 7, 8]))
    rtr.update(Route("2.2.2.2", "20.0.0.0", 16, [44, 55]))
    nh = rtr.next_hop("20.0.12.0")
    print(f"Next hop for 20.0.12.0: {nh}")
    assert nh == "2.2.2.2"

    print("=== Test 12: Handling route withdrawal correctly ===")
    rtr.update(Route("1.1.1.1", "20.0.12.0", 24, [44, 55, 66, 77, 88]))
    nh = rtr.next_hop("20.0.12.0")
    print(f"Next hop for 20.0.12.0 before withdrawal: {nh}")
    assert nh == "1.1.1.1"

    rtr.withdraw(Route("1.1.1.1", "20.0.12.0", 24, [44, 55, 66, 77, 88]))
    nh = rtr.next_hop("20.0.12.0")
    print(f"Next hop for 20.0.12.0 after withdrawal: {nh}")
    assert nh == "2.2.2.2"
    

if __name__ == "__main__":
    test_cases()
   
