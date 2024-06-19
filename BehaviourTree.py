import threading 

FAILURE=0
SUCCESS=1
RUNNING=2

#######################################################################################################################################################################
class Behave:
    def __init__(self,tree_structure):
        self.structure = tree_structure
        for id in tree_structure:
            if len(tree_structure[id]['parents'])==0:
                self.root = id
                break
    #starts of the root node and returns of the total process ended in a SUCCESS or FAILURE
    def tick(self):
        return Node(self.structure,self.root).process()
    
    #set action function for the action node
    def set_action(self,action_node_id,action_function):
        self.structure[action_node_id]["action"]=action_function

    #set condition function for condition node
    def set_condition(self,condition_node_id,condition_function):
        self.structure[condition_node_id]["condition"]=condition_function
    
#######################################################################################################################################################################

class Node:
    #behaviour_structure - structure of the entire behaviour
    #node_structure - structure of the current node
    #id - id of node, integer
    #parents - list of id of parents of the node
    #children - list of id of children of this node
    #status - defines the status of the node(RUNNING,SUCCESS or FAILURE)

    global states
    states=[]
    
    def __init__(self,structure_dict,id):
        self.id = id
        self.behaviour_structure = structure_dict 
        self.node_structure = structure_dict[id]
        self.parents = self.node_structure["parents"] 
        self.children = self.node_structure["children"]
        self.status=RUNNING
        print(self.node_structure['comment'])
        
    #initiates the process of the node
    def process(self,threads=False):
        type = self.node_structure["type"]
        if type=="selector":
            state=selector(self)
        elif type=="sequence":
            state=sequence(self)
        elif type=="parallel":
            state=parallel(self)
        elif type=="inverter":
            state=inverter(self)
        elif type=="succeeder":
            state=succeeder(self)
        elif type=="repeater":
            state=repeater(self)
        elif type=="repeater_forever":
            state=repeater_forever(self)
        elif type=="repeat_till_success":
            state=repeat_till_success(self)
        elif type=="repeat_till_failure":
            state=repeat_till_failure(self)
        elif type=="action":
            state=action(self)
        elif type=="condition":
            state=condition(self)
        else:
            raise Exception("Node type=",type,"does not exists")
        
        if threads==False:
            return state
        else:
            global states
            states.append(state)

#######################################################################################################################################################################
#COMPOSITE NODE FUNCTIONS

def selector(self):
    if len(self.children)>0:
        i=0
        for child in self.children:
            state = Node(self.behaviour_structure,child).process()
            if state==SUCCESS:
                self.status=SUCCESS
                return self.status
            elif i==(len(self.children)-1):
                self.status=FAILURE
                return self.status
            elif i<len(self.children):
                self.status = RUNNING
                i+=1
            
    else:
        raise Exception("Error: Zero children for selector node")

def sequence(self):
    if len(self.children)>0:
        for child in self.children:
            state = Node(self.behaviour_structure,child).process()
            if state==SUCCESS:
                self.status=RUNNING
            elif state==FAILURE:
                self.status = FAILURE
                return self.status
        self.status=SUCCESS
        return self.status
    else:
        raise Exception("Error: Zero children for sequence node")

def parallel(self):
    global states
    child_nodes=[]
    threads=[]
    results=[]
    for id in self.children:
        node = Node(self.behaviour_structure,id,threads=True)
        child_nodes.append(node)
        thread = threading.Thread(target=node.process)
        threads.append(thread)
        thread.start()
    for i in range(len(threads)):
        threads[i].join()
        if FAILURE in states: 
            return FAILURE
        else:
            return SUCCESS

#######################################################################################################################################################################
#DECORATOR NODE FUNCTIONS   
  
def inverter(self):
    state = Node(self.behaviour_structure,self.children[0]).process()
    if state==SUCCESS:
        return FAILURE
    elif state==FAILURE:
        return SUCCESS

def succeeder(self):
    return SUCCESS

def repeater(self):
    node=Node(self.behaviour_structure,self.children[0])
    for i in range(self.node_structure["reps"]-1):
        node.process()
    return node.process()

def repeater_forever(self):
    node=Node(self.behaviour_structure,self.children[0])
    while True:
        node.process()

def repeat_till_success(self):
    node=Node(self.behaviour_structure,self.children[0])
    while True:
        state=node.process()
        if state==SUCCESS:return SUCCESS

def repeat_till_failure(self):
    node=Node(self.behaviour_structure,self.children[0])
    while True:
        state=node.process()
        if state==FAILURE:return FAILURE

#######################################################################################################################################################################
#LEAF NODE FUNCTIONS

def action(self):
    return self.node_structure['action']()

def condition(self):
    return self.node_structure['condition']()
