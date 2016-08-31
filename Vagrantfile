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
      node.vm.provision "shell" do |s|
        s.path =  "scripts/apply_config.sh"
        s.args = ["/home/vagrant/rtr_config1"]
      end
    end
    # PoP router
    config.vm.define "rtr2" do |node|
      node.vm.box =  "IOS XRv"
      # gig0/0/0/0 connected to link1, gig0/0/0/1 connected to link2, auto-config not supported
      node.vm.network :private_network, virtualbox__intnet: "link1", auto_config: false
      node.vm.network :private_network, virtualbox__intnet: "link2", auto_config: false
      node.vm.network "forwarded_port", guest: 58822, host: 58822
      node.vm.provision :shell, path: "scripts/iperf.sh"
      # Launch the container
      node.vm.provision "file", source: "configs/demo.xml", destination: "/home/vagrant/demo.xml"
      node.vm.provision :shell, path: "scripts/launch_container.sh"
      # Apply the XR configuration
      node.vm.provision "file", source: "configs/rtr_config2", destination: "/home/vagrant/rtr_config2"
      node.vm.provision "shell" do |s|
        s.path =  "scripts/apply_config.sh"
        s.args = ["/home/vagrant/rtr_config2"]
      end
    end

    # Internet "router"
    config.vm.define "devbox" do |node|
      node.vm.box =  "ubuntu/trusty64"
      node.vm.network :private_network, virtualbox__intnet: "link2", ip: "11.1.1.20"
      node.vm.provision :shell, path: "scripts/bootstrap_devbox.sh", privileged: false
    end
end
