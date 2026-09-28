class Getjwttoken < Formula
  desc "Retrieve JWT tokens using credentials stored in macOS Keychain"
  homepage "https://github.com/jplonghi/homebrew-tools"
  url "https://raw.githubusercontent.com/jplonghi/homebrew-tools/v1.1.0/getjwttoken"
  sha256 "2a487ed5f77f0442c6ac8c29808d60c7dac3ded9f6d3764744a411f2aae100a2"

  depends_on :macos

  def install
    bin.install "getjwttoken"
  end

  test do
    profile = testpath/"profile"
    profile.write "# Existing configuration\n"

    system bin/"getjwttoken", "--install-profile", "TEST_TOKEN", profile
    installed_profile = profile.read
    assert_match "# Existing configuration\n", installed_profile
    assert_match "export TEST_TOKEN", installed_profile
    assert_match "--print", installed_profile

    system bin/"getjwttoken", "--install-profile", "TEST_TOKEN", profile
    assert_equal installed_profile, profile.read

    assert_match "Invalid variable name", shell_output(
      "#{bin}/getjwttoken --install-profile MY-TOKEN #{profile} 2>&1", 1
    )
  end
end
