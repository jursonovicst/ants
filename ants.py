#!/usr/bin/env python3

import argparse
from ants import Colony, Nest, Queen
import multiprocessing

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='Ants', description="Ants load tester.")
    parser.add_argument('--listen', type=str, metavar='address', help="Master mode, listens for slave connections at.")
    parser.add_argument('--connect', type=str, nargs='+', metavar=('address', 'name'),
                        help="Slave mode, connects to master at 'address' with 'name' identifier.")
    parser.add_argument('--port', type=int, help='Port to use for connection (default: %(default)s)', default=7777)
    parser.add_argument('--nestcount', type=int, help='Number of nests to create per host (default: number of cores -2)'
                        , default=0)
    parser.add_argument('--loglevel', type=str, choices=Nest.LOGLEVELS.keys(),
                        default=list(Nest.LOGLEVELS.keys())[list(Nest.LOGLEVELS.values()).index(Nest.INFO)],
                        help='Log verbosity.')
    parser.add_argument('profile', type=argparse.FileType('r'), nargs='?',
                        help="Python file containing a subclass of the Queen class to describe the load profile.")

    args = parser.parse_args()

    mycolony = None
    mynests = []

    MSTANDALONE = 0
    MMASTER = 1
    MSLAVE = 2

    mode = MSTANDALONE
    if args.connect is not None:
        mode = MSLAVE
    elif args.listen is not None:
        mode = MMASTER

    try:
        if mode == MSLAVE:
            print("Running mode: slave")
            for i in range(0, (multiprocessing.cpu_count() - 2) if args.nestcount is 0 else args.nestcount):
                mynests.append(Nest(address=args.connect[0], port=args.port, loglevel=Nest.LOGLEVELS[args.loglevel],
                                    name="%s_%d" % (args.connect[1] if len(args.connect) > 1 else 'default', i)))

            # wait till all ends, this will block
            for nest in mynests:
                if nest.is_alive():
                    nest.join()

            # done
            exit(0)

        elif mode == MMASTER:
            print("Running mode: master")
            mycolony = Colony(address=args.listen, port=args.port)

            # wait for user to connect nests
            input("Connect slaves, then press enter to execute...")

            # continue to load

        else:
            print('Running mode: standalone')
            mycolony = Colony(address='127.0.0.1', port=args.port)

            for i in range(0, (multiprocessing.cpu_count() - 2) if args.nestcount is 0 else args.nestcount):
                nest = Nest(address='127.0.0.1', port=args.port, loglevel=Nest.LOGLEVELS[args.loglevel],
                            name="%s_%d" % ('default', i))
                mynests.append(nest)

            # continue to load

        # load Queen
        if 'profile' not in args:
            raise AttributeError("Master and standalone mode needs the profile argument!")

        exec(args.profile.read())
        if len(Queen.__subclasses__()) != 1:
            raise SyntaxError("Profile file '%s' must contain exactly one subclass of Queen, found: %s" % (
                args.profile.name, list(map(lambda cls: cls.__name__, Queen.__subclasses__()))))

        # lay the eggs
        myqueen = Queen.__subclasses__()[0]()
        for egg in myqueen.layeggs():
            mycolony.addegg(egg)

        # execute
        mycolony.execute()

        # wait till ends, this will block
        mycolony.join()

    except Exception as e:
        print(e)

        if mycolony:
            mycolony.terminate()
        else:
            # terminate nests if any
            for nest in mynests:
                if nest.is_alive():
                    nest.terminate()

    except KeyboardInterrupt:
        # terminate Colony if any, Colony will terminate its Nests
        if mycolony:
            mycolony.terminate()
        else:
            # terminate nests if any
            for nest in mynests:
                if nest.is_alive():
                    nest.terminate()
