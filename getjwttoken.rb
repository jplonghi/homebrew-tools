# File: getjwttoken.rb

class Getjwttoken < Formula
    desc "A tool to securely retrieve JWT tokens"
    homepage "https://github.com/jplonghi/homebrew-tools"
    url "https://github.com/jplonghi/homebrew-tools/archive/refs/tags/v1.0.0.tar.gz"
    version "1.0.0"
    sha256 "6e28c421b4ab448d19e6d529107dc8eccee91ad540d4df01d7920151ef14fe85"
  
    def install
      bin.install "getjwttoken"

      # Ensure the script is executable
      chmod "+x", bin/"getjwttoken"
    end
  end
  