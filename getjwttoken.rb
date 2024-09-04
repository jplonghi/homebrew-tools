# File: getjwttoken.rb

class Getjwttoken < Formula
    desc "A tool to securely retrieve JWT tokens"
    homepage "https://github.com/jplonghi/homebrew-tools"
    url "https://github.com/jplonghi/homebrew-tools/archive/refs/tags/v1.0.tar.gz"
    version "1.0.0"
    sha256 "cade549ae79c6fb94e6d1455a93c7dc433683c197dce7f190703d80fc362f8d7"
  
    def install
      bin.install "getjwttoken"

      # Ensure the script is executable
      chmod "+x", bin/"getjwttoken"
    end
  end
  