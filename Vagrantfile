# -*- mode: ruby -*-

# vi: set ft=ruby :

Vagrant.configure(2) do |config|

    # Data Center router
    config.vm.define "rtr1" do |node|
      node.vm.box =  "IOS XRv"
      # gig0/0/0/0 connected to link1, auto-config not supported.
      node.vm.network :private_network, virtualbox__intnet: "link1", auto_config: false
      node.vm.provision :shell, path: "scripts/iperf.sh"
      node.vm.provision "file", source: "configs/rtr_config1", destination: "/home/vagrant/rtr_config1"
      # Make sure virtualbox nics are set to promiscuous mode for a bridge node
      node.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--nicpromisc2", "allow-all"]
      end
      node.vm.provision "shell" do |s|
        s.path =  "scripts/apply_config.sh"
        s.args = ["/home/vagrant/rtr_config1"]
      end
      node.vm.provision "shell", inline: "nohup iperf -s -B 10.1.1.2 -u &"
      node.vm.provision "shell", inline: "nohup iperf -s -B 5.5.5.5 -u &"
    end

    # Bridge between rtr1 and rtr2
    config.vm.define "bridge" do |node|
      node.vm.box =  "ubuntu/trusty64"

      # eth1 and eth2 connected to rtr1  and  eth3 and eth4  connected to rtr2
      node.vm.network :private_network, virtualbox__intnet: "link1", auto_config: false
      node.vm.network :private_network, virtualbox__intnet: "link2", auto_config: false

      # Important! For this node to act as a bridge, All the virtualbox interfaces must be in promiscuous mode.
      node.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--nicpromisc2", "allow-all"]
        vb.customize ["modifyvm", :id, "--nicpromisc3", "allow-all"]
      end

      # Transfer all the impairment helper scripts to cause network degradation, later
      node.vm.provision "start_impair", type: "file", source: "scripts/start_impair.sh", destination: "/home/vagrant/start_impair.sh"
      node.vm.provision "stop_impair", type: "file", source: "scripts/stop_impair.sh", destination: "/home/vagrant/stop_impair.sh"

      # Set up the bridge interfaces
      node.vm.provision "setup_devbox", type: "shell" do |s|
          s.path =  "scripts/bridge_setup.sh"
      end
    end
    # PoP router
    config.vm.define "rtr2" do |node|
      node.vm.box =  "IOS XRv"
      node.vm.network :private_network, virtualbox__intnet: "link2", auto_config: false
      node.vm.network :private_network, virtualbox__intnet: "link3", auto_config: false
      node.vm.provider "virtualbox" do |v|
            v.customize ["modifyvm", :id, "--nic4", "natnetwork", "--nat-network4", "Internet"]
      end
      node.vm.network "forwarded_port", guest: 58822, host: 58822
      #Provision iperf.
      node.vm.provision :shell, path: "scripts/iperf.sh"
      # Launch the container
      node.vm.provision "file", source: "configs/demo.xml", destination: "/home/vagrant/demo.xml"
      node.vm.provision :shell, path: "scripts/launch_container.sh"
      # Apply the XR configuration
      node.vm.provision "file", source: "configs/rtr_config2", destination: "/home/vagrant/rtr_config2"
      # Make sure virtualbox nics are set to promiscuous mode for a bridge node
      node.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--nicpromisc3", "allow-all"]
      end
      node.vm.provision "shell" do |s|
        s.path =  "scripts/apply_config.sh"
        s.args = ["/home/vagrant/rtr_config2"]
      end
    end

    # Internet "router"
    config.vm.define "devbox" do |node|
      node.vm.box =  "ubuntu/trusty64"
      node.vm.network :private_network, virtualbox__intnet: "link3", ip: "11.1.1.20"
      node.vm.provision :shell, path: "scripts/bootstrap_devbox.sh", privileged: false
    end

end
